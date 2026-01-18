# Load Testing Strategy for the Liquorfy Application

## 1. Objective

The primary goal of this load testing strategy is to understand the performance limits and identify bottlenecks of the Liquorfy application running on an 8GB RAM VPS. We aim to answer the following questions:

- What is the maximum number of requests per second (RPS) the application can handle before performance degrades?
- How does the system behave under different types of workloads (e.g., read-heavy vs. write-heavy)?
- What is the breaking point of the database vs. the API server?
- Is the 8GB RAM of the VPS sufficient for our expected traffic?

## 2. Key Metrics

We will monitor the following metrics to evaluate performance.

### Application Metrics (from Locust)
- **Requests Per Second (RPS):** Total throughput of the system.
- **Response Time (Average):** The average time for a request to complete.
- **Response Time (95th/99th Percentile):** The response time that 95% or 99% of users experience. This is more important than the average for gauging user experience.
- **Error Rate (%):** The percentage of requests that fail (e.g., HTTP 5xx errors).

### System Metrics (from the VPS)
- **CPU Utilization (%):** To see if we are CPU-bound.
- **Memory Usage (GB):** To see if we are running out of RAM.
- **I/O Wait (%):** To identify if performance is limited by disk speed (often related to the database).

## 3. Recommended Tool

We will use **[Locust](https://locust.io/)**, a modern, open-source load testing tool. It is written in Python, making it easy to create test scripts that simulate realistic user behavior.

**Installation:**
```bash
pip install locust
```

## 4. Test Scenarios

We will simulate different user behaviors to test the system under various conditions.

### Scenario 1: High Read-Throughput (Best-Case)
This test simulates a high number of users browsing known products. It is designed to test the performance of the **caching layer (Redis)** and the API workers. We expect a very high cache hit ratio.

- **User Behavior:** Users repeatedly request the first few pages of products and a list of stores.
- **Goal:** Determine the maximum RPS the application can serve from its cache.

### Scenario 2: Mixed Realistic Workload
This test simulates a more realistic traffic pattern with a mix of browsing, searching, and writing data (e.g., adding to a cart).

- **User Behavior (weighted):**
    - 70% of requests are browsing products (high cache hit).
    - 20% of requests are using the search functionality with random terms (low cache hit).
    - 10% of requests are writing data (e.g., `POST` to a cart/favorites endpoint, zero cache hit).
- **Goal:** Understand how the system performs under a realistic load that stresses the cache, the API, and the database simultaneously.

### Scenario 3: Database Stress Test (Worst-Case)
This test is designed to intentionally bypass the cache and put maximum pressure on the **PostgreSQL database**.

- **User Behavior:** Every request is a `GET` request to the search endpoint with a unique, randomly generated search query.
- **Goal:** Find the breaking point of the database and determine the maximum number of un-cached API calls the system can handle.

## 5. Execution Methodology

1.  **Prepare the Environment:**
    - The application should be deployed on the 8GB VPS in its production configuration (`docker-compose.prod.yml`).
    - The database should be seeded with a realistic amount of data.

2.  **Write the Locust Test Script:**
    - Create a file named `locustfile.py`. Below is a starter template for the **Mixed Realistic Workload** scenario.

    ```python
    # locustfile.py
    import random
    import string
    from locust import HttpUser, task, between

    def get_random_string(k=8):
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=k))

    class LiquorfyUser(HttpUser):
        # Users will wait 1-3 seconds between tasks
        wait_time = between(1, 3)

        # Task 1: Browse products (high weight)
        @task(7)
        def browse_products(self):
            # Assumes a product endpoint that supports pagination
            self.client.get("/api/v1/products?page=1&per_page=25", name="/api/v1/products")

        # Task 2: Search for products (medium weight)
        @task(2)
        def search_products(self):
            # Use a random query to reduce cache hits
            search_term = get_random_string()
            self.client.get(f"/api/v1/search?q={search_term}", name="/api/v1/search?q=[query]")

        # Task 3: "Add to cart" simulation (low weight)
        # Replace with your actual write endpoint
        @task(1)
        def add_to_cart(self):
            # This is an example, update with a real product ID and endpoint
            product_id = random.randint(1, 500)
            self.client.post(f"/api/v1/cart", json={"product_id": product_id, "quantity": 1}, name="/api/v1/cart")

    ```

3.  **Run the Test:**
    - Start the Locust web UI from your local machine (or another machine, not the VPS itself).
      ```bash
      locust -f locustfile.py --host=http://your-vps-ip-address
      ```
    - Open your browser to `http://localhost:8089`.
    - Start by simulating a small number of users (e.g., 10) and gradually ramp up the user count every few minutes.

4.  **Monitor System Resources:**
    - While the test is running, SSH into your VPS and use the following commands to monitor resource usage:
      - `htop`: For a real-time overview of CPU and Memory.
      - `docker stats`: To see the resource consumption of each individual container (`api`, `db`, `redis`).

5.  **Analyze Results:**
    - Observe the charts in the Locust UI. Note the RPS and response times as you increase the user load.
    - Identify the point where response times begin to climb rapidly or the error rate increases.
    - Correlate these application metrics with your system resource monitoring. For example, "When the RPS reached 800, the database container's CPU usage hit 100%, and p99 latency spiked to 3000ms."

## 6. Success Criteria

A successful test would be the system achieving a target RPS (e.g., 500 RPS) for the "Mixed Realistic Workload" while maintaining:
- **p99 Response Time:** < 1500ms
- **Error Rate:** < 0.1%
- **CPU Utilization:** < 85%
- **Memory Usage:** A stable level with no swapping.
