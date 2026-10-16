from locust import HttpUser, task, between
import random


class testingCompra(HttpUser):
    wait_time = between(0.1,0.3)

    @task
    def comprarProducto(self):
        payload = {
            "producto_id" : 3
        }

        self.client.post("/productos/3", json=payload)
