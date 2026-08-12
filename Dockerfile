FROM astral/uv:python3.13-trixie-slim

# Install system dependencies
RUN apt update && apt install -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install the project into `/app`
WORKDIR /app

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Omit development dependencies
ENV UV_NO_DEV=1

COPY pyproject.toml uv.lock ./

# Install the project's dependencies using the lockfile and settings
RUN uv sync --locked --no-install-project

COPY . .

RUN uv sync --locked 

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

CMD ["uv", "run", "clean-video-dl"]
