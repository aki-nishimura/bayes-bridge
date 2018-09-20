import numpy as np
import scipy.sparse as sparse
from .abstract_matrix import AbstractMatrix

class DenseMatrix(AbstractMatrix):
    
    def __init__(self, X):
        """
        Params:
        ------
        X : numpy array
        order : str, {'row_major', 'col_major', None}
        """

        self.X = X
        self.format = 'dense'
        self.order = None
        self.shape = self.X.shape

    def dot(self, v):
        return self.X.dot(v)

    def Tdot(self, v):
        return self.X.T.dot(v)

    def toarray(self):
        return self.X

    def extract_matrix(self, order=None):
        return self.X