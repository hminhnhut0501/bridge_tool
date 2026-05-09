#!/bin/bash

# Khởi chạy Scheduler ở chế độ nền (background)
python scheduler.py &

# Khởi chạy Bot chính (tiến trình này sẽ giữ cho Server luôn chạy)
python main.py