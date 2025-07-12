# Collision Detection and Awareness System
An intelligent system for rear vehicle detection, tracking, and speed estimation using YOLOv8, DeepSORT, and homography. It provides visual lane zone classification (green/yellow/red) and real-time audio-visual alerts to help prevent collisions. The GUI is built with Tkinter.

## 🚀 Features

- Detects vehicles (car, truck, motorcycle, bus) using YOLOv8
- Tracks vehicle movement using DeepSORT
- Estimates real-world speed using homography and bounding box tracking
- Classifies zones into:
  - 🟢 Green (Safe)
  - 🟡 Yellow (Caution)
  - 🔴 Red (Danger)
- Shows traffic-light indicators in the GUI
- Plays audio alerts for yellow/red zones
- Built-in video player using Tkinter
