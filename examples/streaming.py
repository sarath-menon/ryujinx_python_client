from ryujinx_python_client import GameController
import matplotlib.pyplot as plt

controller = GameController()
controller.connect_websockets()

img = controller.get_screenshot()
controller.close_websockets()

plt.imshow(img)
plt.show()



