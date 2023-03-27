# import jax and check if cuda is available
import jax

# check if cuda is available
cuda_available = jax.lib.xla_bridge.get_backend().platform == "gpu"
print(f"CUDA is available: {cuda_available}")

