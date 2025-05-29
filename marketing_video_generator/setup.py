from setuptools import setup, find_packages

setup(
    name="marketing_video_generator",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn[standard]",
        "moviepy",
        "Pillow",
        "requests",
    ],
) 