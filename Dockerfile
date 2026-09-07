# পাইথনের অফিশিয়াল লাইটওয়েট ভার্সন ব্যবহার করছি
FROM python:3.10-slim

# কাজের ফোল্ডার সেট করা
WORKDIR /app

# প্রজেক্টের সব ফাইল ডকারে কপি করা
COPY . /app

# aiogram এবং আপনার দরকারি সব লাইব্রেরি একবারে ইনস্টল করা
RUN pip install --no-cache-dir aiogram pydantic

# বট রান করার কমান্ড (আপনার পাইথন ফাইলের নাম যদি main.py না হয়ে অন্য কিছু হয়, তবে main.py এর জায়গায় আপনার ফাইলের নাম দেবেন)
CMD ["python", "main.py"]
