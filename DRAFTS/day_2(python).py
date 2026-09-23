"""NOW STARTING NUMPY AND PANDAS AND DATA CLEANING , PROCESSING"""
import numpy as np
#creation
arr=np.array([1,2,3,4,5,6])
matrix = np.array([[1, 2, 3], [4, 5, 6]])
print(f"Shape: {matrix.shape}")
print(f"Size: {matrix.size}")
print(f"Dtype: {matrix.dtype}")
# Useful for DE
zeros = np.zeros((3, 4))      # Initialize empty data
ones = np.ones((5, 2))         # Initialize with default
random = np.random.rand(3, 3)  # Generate test data
# Reshaping - مهم في batch processing
data = np.arange(24)           # [0, 1, 2, ..., 23]
batches = data.reshape(4, 6)   # 4 batches, 6 items each
print(f"Batches shape: {batches.shape}")
# Vectorized operations (بدل loops!)
prices = np.array([100, 200, 300, 400])
discounted = prices * 0.85      # [85, 170, 255, 340]
print(f"Discounted: {discounted}")
# Boolean indexing - filtering
sales = np.array([500, 1200, 800, 2000, 300])
high_sales = sales[sales > 1000]
print(f"High sales: {high_sales}")
# Aggregation
print(f"Total: {sales.sum()}")
print(f"Average: {sales.mean()}")
print(f"Max: {sales.max()}") 