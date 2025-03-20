from venumML.linear_models.regression.linear_regression import EncryptedLinearRegression
from custom_nesterov import CustomNesterov  
from venumML.venumpy import small_glwe as vp
from venumML.venum_tools import *


class CustomEncryptedLinearRegression(EncryptedLinearRegression):
    def __init__(self, ctx, project_id, topic_id):
        """
        Initialize the custom encrypted linear regression model.

        Parameters
        ----------
        ctx : EncryptionContext
            The encryption context used for encryption and decryption.
        project_id : str
            GCP project ID.
        topic_id : str
            GCP Pub/Sub topic ID where loss values will be published.
        """
        super().__init__(ctx)  # Initialize the parent class
        self.project_id = project_id
        self.topic_id = topic_id

    def encrypted_fit(self, ctx, x, y, lr=0.3, gamma=0.9, epochs=10):
        """
        Train the model using the custom optimizer that publishes losses.
        """
        self.optimizer = CustomNesterov(self._context, self.project_id, self.topic_id, lr, gamma, epochs)  

        encrypted_intercept, encrypted_coef, losses = self.optimizer.venum_nesterov_agd(ctx, x, y)
        self._encrypted_intercept_ = encrypted_intercept
        self._encrypted_coef_ = encrypted_coef
