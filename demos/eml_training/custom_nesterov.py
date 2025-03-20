import json
import time
import numpy as np
from google.cloud import pubsub_v1

from venumML.venum_tools import *
from venumML.optimization.sgd import Nesterov

class CustomNesterov(Nesterov):
    def __init__(self, ctx, project_id, topic_id, lr=0.3, gamma=0.9, epochs=10):
        """
        Initializes CustomNesterov with Pub/Sub setup.

        Parameters
        ----------
        ctx : EncryptionContext
            The encryption context used to encrypt values.
        project_id : str
            GCP project ID.
        topic_id : str
            GCP Pub/Sub topic ID where loss values will be published.
        """
        lr = lr
        gamma = gamma
        epochs = epochs
        super().__init__(ctx, lr, gamma, epochs)
        self.project_id = project_id
        self.topic_id = topic_id
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(self.project_id, self.topic_id)

    def publish_loss(self, loss, epoch):
        """
        Publishes the loss value to a GCP Pub/Sub topic.

        Parameters
        ----------
        loss : float
            The loss value at the given epoch.
        epoch : int
            The epoch number.
        """
        message_data = {"epoch": epoch, "loss": self._context.decrypt(loss)} # TODO: implement the decryption using dummy PRE scheme in google cloud functions
        message_json = json.dumps(message_data).encode("utf-8")
        future = self.publisher.publish(self.topic_path, message_json)
        future.result()  # Ensures the message is sent

    def venum_nesterov_agd(self, ctx, x, y):
        """
        Applies Nesterov's Accelerated Gradient Descent and publishes loss values.
        """
        if x.ndim == 1:
            x = x.reshape(-1, 1)  
        if y.ndim == 1:
            y = y.reshape(-1, 1)  
        
        n_samples, n_features = x.shape        
        w = np.random.randn(n_features, 1) * np.sqrt(1 / n_features)
        b = np.random.randn()
        
        w = encrypt_array(w, ctx)
        b = ctx.encrypt(b)
        lr = ctx.encrypt(self._lr)
        gamma = ctx.encrypt(self._gamma)
    
        velocity_w = encrypt_array(np.zeros((n_features, 1)), ctx)
        velocity_b = ctx.encrypt(0)
        
        losses = []
        
        for i in range(self._epochs):
            w_look_ahead = w - velocity_w * gamma
            b_look_ahead = b - velocity_b * gamma
            y_pred = x @ w_look_ahead + b_look_ahead  
            error = y_pred - y
            loss = np.mean(error**2)
            losses.append(loss)

            # Publish loss to GCP Pub/Sub
            self.publish_loss(loss, i)

            grad_w = np.mean(x * error, axis=0, keepdims=True).T
            grad_b = np.mean(error)
            
            velocity_w = velocity_w * gamma + grad_w * lr
            velocity_b = velocity_b * gamma + grad_b * lr

            w = w - velocity_w
            b = b - velocity_b
        
        encrypted_intercept = b_look_ahead
        encrypted_coef = np.atleast_1d(w_look_ahead.squeeze())
        
        return encrypted_intercept, encrypted_coef, losses
