import numpy as np
# إنشاء array
a = np.array([1, 2, 3, 4, 5])
print(a)              # [1 2 3 4 5]
print(a.ndim)         # 1 (عدد الأبعاد)
print(a.shape)        # (5,) (الشكل)
print(a.dtype)        # int64 (نوع البيانات)
# Array ثنائي الأبعاد (Matrix)
b = np.array([[1, 2, 3], [4, 5, 6]], dtype=np.float32)
print(b.shape)        # (2, 3) - 2 صفوف، 3 أعمدة
print(b.ndim)         # 2
# Arrays جاهزة
zeros = np.zeros((3, 3))           # مصفوفة أصفار
ones = np.ones((2, 4))             # مصفوفة واحدات
identity = np.eye(3)               # مصفوفة وحدة (diagonal = 1)
# Ranges
arr = np.arange(0, 10, 2)          # [0, 2, 4, 6, 8]
lin = np.linspace(0, 1, 5)         # [0, 0.25, 0.5, 0.75, 1]
# Random
random_arr = np.random.random((3, 3))      # أرقام عشوائية بين 0 و 1
rand_int = np.random.randint(0, 100, (2, 3))  # أرقام صحيحة عشوائية
# من قائمة موجودة
python_list = [1, 2, 3, 4, 5]
numpy_arr = np.array(python_list)
a = np.array([1, 2, 3, 4, 5, 6])
# Reshape
b = a.reshape(2, 3)        # [[1,2,3], [4,5,6]]
c = a.reshape(3, -1)       # -1 يعني "احسبها تلقائياً" → (3, 2)
# Flatten (تسطيح)
flat = b.ravel()           # [1, 2, 3, 4, 5, 6]
# Transpose (الانعكاس)
d = np.array([[1, 2], [3, 4], [5, 6]])
print(d.T)                 # [[1,3,5], [2,4,6]]
a = np.array([1, 2, 3])
b = np.array([4, 5, 6])
# العمليات element-wise (على كل عنصر)
print(a + b)        # [5, 7, 9]
print(a * b)        # [4, 10, 18]  (ضرب عنصر بعنصر)
print(a ** 2)       # [1, 4, 9]
# Universal Functions (ufuncs)
print(np.sqrt(a))   # [1, 1.414, 1.732]
print(np.exp(a))    # [2.718, 7.389, 20.085]
print(np.log(a))    # [0, 0.693, 1.099]
# إحصائيات
arr = np.array([[1, 2, 3], [4, 5, 6]])
print(arr.sum())           # 21
print(arr.sum(axis=0))     # [5, 7, 9] - sum لكل عمود
print(arr.sum(axis=1))     # [6, 15] - sum لكل صف
print(arr.mean())          # 3.5
print(arr.std())           # الانحراف المعياري
print(arr.min(), arr.max())
arr = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
# Indexing
print(arr[0, 0])       # 1 (أول صف، أول عمود)
print(arr[0, -1])      # 3 (أول صف، آخر عمود)
print(arr[0, :])       # [1, 2, 3] (الصف الأول كله)
print(arr[:, 0])       # [1, 4, 7] (العمود الأول كله)
# Slicing
print(arr[1:3, 1:3])   # [[5,6], [8,9]] - sub-matrix
# Boolean Indexing (الأقوى!)
print(arr[arr > 5])    # [6, 7, 8, 9] - كل القيم > 5
arr[arr < 3] = 0       # استبدال القيم < 3 بـ 0
# Broadcasting: العمليات على arrays بأحجام مختلفة
a = np.array([[1, 2, 3], [4, 5, 6]])  # shape: (2, 3)
b = np.array([10, 20, 30])             # shape: (3,)
# b تتمدد تلقائياً لتصبح (2, 3)
print(a + b)
# [[11, 22, 33],
#  [14, 25, 36]]
# مثال: إضافة قيمة لكل عنصر
print(a + 5)
# [[6, 7, 8],
#  [9, 10, 11]]