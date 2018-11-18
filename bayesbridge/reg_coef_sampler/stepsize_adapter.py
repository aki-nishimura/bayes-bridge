from math import exp, log, sqrt
from bayesbridge.util import warn_message_only

class StepsizeAdapter():

    def __init__(self, init_stepsize, target_accept_prob=.9,
                 init_adaptsize=1., adapt_decay_exponent=1.,
                 reference_iteration=100, adaptsize_at_reference=.05):
        """
        Parameters
        ----------
        reference_iteration & adaptsize_at_reference:
            Stepsize sequence of Robbins-Monro algorithm will be set so that it
            decreases to `adaptsize_at_refrence` after `reference_iteration`.
        """
        if init_stepsize <= 0:
            raise ValueError("The initial stepsize must be positive.")
        log_init_stepsize = log(init_stepsize)
        self.log_stepsize = log_init_stepsize
        self.log_stepsize_averaged = log_init_stepsize
        self.n_averaged = 0
        self.target_accept_prob = target_accept_prob

        self.rm_stepsize = iter(RobbinsMonroStepsize(
            init=init_adaptsize,
            decay_exponent=adapt_decay_exponent,
            reference_iteration=reference_iteration,
            size_at_reference=adaptsize_at_reference
        ))

    def get_current_stepsize(self, averaged=False):
        if averaged:
            return exp(self.log_stepsize_averaged)
        else:
            return exp(self.log_stepsize)

    def adapt_stepsize(self, accept_prob):
        self.n_averaged += 1
        rm_stepsize = next(self.rm_stepsize)
        self.log_stepsize += rm_stepsize * (accept_prob - self.target_accept_prob)
        weight = 1 / self.n_averaged
        self.log_stepsize_averaged = (
            weight * self.log_stepsize
            + (1 - weight) * self.log_stepsize_averaged
        )
        return exp(self.log_stepsize)


class RobbinsMonroStepsize():

    def __init__(self, init=1., decay_exponent=1.,
                 reference_iteration=None, size_at_reference=None):
        self.init = init
        self.exponent = decay_exponent
        self.scale = self.determine_decay_scale(
            init, decay_exponent, reference_iteration, size_at_reference
        )

    def determine_decay_scale(self, init, decay_exponent, ref_iter, size_at_ref):

        if (ref_iter is not None) and (size_at_ref is not None):
            decay_scale = \
                ref_iter / ((init / size_at_ref) ** (1 / decay_exponent) - 1)
        else:
            warn_message_only(
                'The default stepsize sequence tends to decay too quicky; '
                'consider manually setting the decay scale.'
            )
            decay_scale = 1.

        return decay_scale

    def __iter__(self):
        self.n_iter = 0
        return self

    def __next__(self):
        stepsize = self.calculate_stepsize(self.n_iter)
        self.n_iter += 1
        return stepsize

    def calculate_stepsize(self, n_iter):
        stepsize = self.init / (1 + n_iter / self.scale) ** self.exponent
        return stepsize


class DualAverageStepsizeAdapter():

    def __init__(self, init_stepsize, target_accept_prob=.9):

        if init_stepsize <= 0:
            raise ValueError("The initial stepsize must be positive.")
        log_init_stepsize = log(init_stepsize)
        self.log_stepsize = log_init_stepsize
        self.log_stepsize_averaged = log_init_stepsize
        self.n_averaged = 0
        self.target_accept_prob = target_accept_prob
        self.latent_stat = 0.  # Used for dual-averaging.

        # Parameters for the dual-averaging algorithm.
        self.stepsize_averaging_log_decay_rate = 0.75
        self.latent_prior_samplesize = 10
        multiplier = 2. # > 1 to err on the side of shrinking toward a larger value.
        self.log_stepsize_shrinkage_mean = log(multiplier) + log_init_stepsize
        self.log_stepsize_shrinkage_strength = 0.05
            # Variable name is not quite accurate since this parameter interacts with latent_prior_samplesize.

    def get_current_stepsize(self, averaged=False):
        if averaged:
            return exp(self.log_stepsize_averaged)
        else:
            return exp(self.log_stepsize)

    def adapt_stepsize(self, accept_prob):
        self.n_averaged += 1
        self.latent_stat = self.update_latent_stat(
            accept_prob, self.target_accept_prob, self.latent_stat
        )
        self.log_stepsize, self.log_stepsize_averaged = self.dual_average_stepsize(
            self.latent_stat, self.log_stepsize_averaged
        )
        return exp(self.log_stepsize)

    def update_latent_stat(self, accept_prob, target_accept_prob, latent_stat):
        weight_latent = (self.n_averaged + self.latent_prior_samplesize) ** -1
        latent_stat = (1 - weight_latent) * latent_stat \
                      + weight_latent * (target_accept_prob - accept_prob)
        return latent_stat

    def dual_average_stepsize(self, latent_stat, log_stepsize_optimized):
        log_stepsize = (
            self.log_stepsize_shrinkage_mean
            - sqrt(self.n_averaged) / self.log_stepsize_shrinkage_strength * latent_stat
        )
        weight = self.n_averaged ** - self.stepsize_averaging_log_decay_rate
        log_stepsize_optimized = \
            (1 - weight) * log_stepsize_optimized + weight * log_stepsize
        return log_stepsize, log_stepsize_optimized