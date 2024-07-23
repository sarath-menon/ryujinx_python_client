import numpy as np
import gradio as gr
from PIL import Image
import requests
from io import BytesIO
from game_control import GameController
from models import GPTModels, Florence2Model, markdown_to_dict
import base64
import asyncio
import datetime
import os
import json
import time
import cv2

URL = "http://localhost:8086/screenshot"
PROMPT_PATH = "prompts/mario-odessey.md"
prompts_dict = markdown_to_dict(PROMPT_PATH)
system_prompt = prompts_dict['system_prompt']

gc = GameController()
model = GPTModels(system_prompt)

florence_model = Florence2Model()

from dataclasses import dataclass

@dataclass
class GameData:
    selected_model: str = "gpt-4o-img"
    is_auto_execute: bool = False
config = GameData()

images_list = [{"files": ["/Users/sarathmenon/Documents/master_thesis/datasets/game_dataset/raw/fortnite/1.jpg"], "text": "Please pay attention to the movement of the object from the first image to the second image, then write a HTML code to show this movement."}]

def image_to_base64(pil_image):
    # Convert PIL Image to bytes directly
    buffered = BytesIO()
    pil_image.save(buffered, format="WEBP")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

async def get_bboxes(image_array, text_input):

    print("text_input:", text_input)

    text_input = "locate the ladder"
    image = Image.fromarray(image_array)

    # phrase grounded detection
    task_prompt = '<CAPTION_TO_PHRASE_GROUNDING>'
    results = florence_model.run_example(image, task_prompt, text_input=text_input)
    bbox_image = florence_model.get_bbox_image(image, results['<CAPTION_TO_PHRASE_GROUNDING>'])
    return bbox_image

async def save_image_and_response(image_array, response):
    # Create a directory with the current date and time
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    directory_path = os.path.join("logs", current_time)
    os.makedirs(directory_path, exist_ok=True)
    
    # Save the image
    img = Image.fromarray(image_array)
    img = img.convert('RGB')
    img.save(os.path.join(directory_path, "screenshot.jpeg"), "JPEG")
    
    # Save the response
    response_path = os.path.join(directory_path, "response.txt")
    with open(response_path, "w") as file:
        file.write(response)
    
    print(f"Saved image and response in {directory_path}")


async def do_action(action, direction=None):
    if action == "move_player":
        gc.move_player(direction)
    elif action == "orbit_camera":
        gc.orbit_camera(direction)
    elif action == "throw_hat":
        gc.special_action(action)
    elif action == "jump":
        gc.special_action(action)
    else:
        print(f"Invalid action: {action}")
        return
    print(f"Doing action: {action}, direction: {direction}")

def update_direction_options(action):
    if action == "move_player":
        return gr.update(choices=["forward", "backward", "left", "right"])
    elif action == "orbit_camera":
        return gr.update(choices=["up", "down", "left", "right"])
    elif action == "collect_treasure":
        return gr.update(choices=["forward", "backward", "left", "right"])
    return gr.update(choices=[])

# Image should be PIL image
async def call_model(text_input, image=None):
    prompts_dict = markdown_to_dict(PROMPT_PATH)
    # system_prompt = prompts_dict['system_prompt']
    # print(system_prompt)
    user_prompt = ''

    if text_input == "take_action_1_step":
        user_prompt = prompts_dict['take_action_1_step']
    elif text_input == "take_action_3_steps":
        user_prompt = prompts_dict['take_action_3_steps']
    elif text_input == "describe_game_state":
        user_prompt = prompts_dict['describe_game_state']
    else:
        user_prompt = text_input + prompts_dict['custom_prompt_extension']

    if config.selected_model == "gpt-4o-img":
        base64_image = image_to_base64(image)
        stream = await model.single_img_response_async(base64_image, user_prompt)
        return stream
    elif config.selected_model == "gpt-3.5":
        return await model.generate_waste_async(user_prompt)
    else:
        print("Model not supported")
        return None

async def chatbox_callback(message, history, dummy_call=True):

    # pause game
    # gc.pause_game()
    img = gc.get_screenshot()

    # call model
    stream = await call_model(message, img)
    if stream is None:
        return
    
    # print response
    response = ""
    async for chunk in stream:
        content = chunk.choices[0].delta.content or ""
        response += content
        yield response

    model.add_response_to_history(response)
    response_json = json.loads(response)

    # take action if auto execute is true
    if config.is_auto_execute:
        await do_action(response_json["action"], response_json["direction"])

def execute_btn_callback(chat_input):
    response = chat_input[-1][-1]
    response_json = json.loads(response)
    print(response_json["action"], response_json["direction/target"])

def object_detection_callback(model, text_input):
    img = gc.get_screenshot()

    if model == "florence_2":
        task_prompt = '<CAPTION_TO_PHRASE_GROUNDING>'
        results = florence_model.run_example(img, task_prompt, text_input=text_input)
        bbox_image = florence_model.get_bbox_image(img, results['<CAPTION_TO_PHRASE_GROUNDING>'])
        return bbox_image, results['<CAPTION_TO_PHRASE_GROUNDING>']['labels']
    elif model == "grounding_dino":
        return img, "selv"
    else:
        return img, "Unsupported model"

philosophy_quotes = [
    ["I think therefore I am."],
    ["The unexamined life is not worth living."]
]

startup_quotes = [
    ["Ideas are easy. Implementation is hard"],
    ["Make mistakes faster."]
]

def predict(im):
    return im["composite"]

with gr.Blocks() as demo:
    gr.Markdown("# Game Screenshot and Response")

    with gr.Column():
        with gr.Tab("Chatbot"):
            chatbot = gr.Chatbot(render=False)            
            chat_input = gr.ChatInterface(
                fn=chatbox_callback,
                examples=["take_action_1_step", "take_action_3_steps", "describe_game_state"],
                chatbot=chatbot,
                retry_btn=None,
                undo_btn=None,
                # clear_btn=None,
            )

            with gr.Row():
                model_select = gr.Dropdown(value="gpt-4o-img", choices=["gpt-4o-img", "gpt-4o-video",
                "gpt4-vision",'llava-1.6',"gpt-3.5"], label="Select model")

                with gr.Column():
                    execute_btn = gr.Button("Execute")
                    auto_execute_checkbox = gr.Checkbox(label="Auto execute")
                    
                
                model_select.change(fn=lambda x: setattr(config, 'selected_model', x), inputs=[model_select], outputs=[])

                auto_execute_checkbox.change(fn=lambda x: setattr(config, 'is_auto_execute', x), inputs=[auto_execute_checkbox], outputs=[])

                execute_btn.click(fn=execute_btn_callback, inputs=[chatbot], outputs=[])

       

        # object detection output
        with gr.Tab("Object Detection"):
            with gr.Column():
                vlm_input = gr.Image(show_label=False)

            with gr.Row():
                with gr.Column():
                    text_input = gr.Textbox(label="Text input", placeholder="Enter a text input")
                
                    obj_detection_dropdown = gr.Dropdown(value="florence_2", choices=["grounding_dino", "florence_2"], label="Select model")
                    submit_button = gr.Button("Submit")

                with gr.Column():
                    obj_detection_output = gr.Textbox(label="Model output")

                submit_button.click(fn=object_detection_callback, inputs=[obj_detection_dropdown, text_input], outputs=[vlm_input, obj_detection_output])

        with gr.Tab("Manual Action"):
            with gr.Column():
                gr.Markdown("## Select action manually")
                action_select = gr.Radio(["move_player", "orbit_camera", "throw_hat", "jump"], label="Select action")

                direction_select = gr.Radio(["forward", "backward", "left", "right"], label="Select direction")

                action_button = gr.Button("Do action")
                action_select.change(fn=update_direction_options, inputs=[action_select], outputs=[direction_select])

                action_button.click(fn=do_action, inputs=[action_select, direction_select])    
        
        with gr.Tab("Dataset"):

            with gr.Row():
                im = gr.ImageEditor(
                    type="numpy",
                    crop_size="1:1",
                )
                im_preview = gr.Image()
            n_upload = gr.Number(0, label="Number of upload events", step=1)
            n_change = gr.Number(0, label="Number of change events", step=1)
            n_input = gr.Number(0, label="Number of input events", step=1)

            im.upload(lambda x: x + 1, outputs=n_upload, inputs=n_upload)
            im.change(lambda x: x + 1, outputs=n_change, inputs=n_change)
            im.input(lambda x: x + 1, outputs=n_input, inputs=n_input)
            im.change(predict, outputs=im_preview, inputs=im, show_progress="hidden")

            with gr.Column():
                chat_input = gr.MultimodalTextbox(interactive=True, file_types=["image","video"], placeholder="Enter message or upload file...", show_label=False)

                gr.Examples(examples=[images_list], inputs=[chat_input], label="Compare images: ")
                

        with gr.Row():
            pause_button = gr.Button("Pause game")
            resume_button = gr.Button("Resume game")
            connect_emulator_btn = gr.Button("Connect emulator")
            disconnect_emulator_btn = gr.Button("Disconnect emulator")

            pause_button.click(fn=gc.pause_game)
            resume_button.click(fn=gc.resume_game)
            connect_emulator_btn.click(fn=gc.connect_websockets)
            disconnect_emulator_btn.click(fn=gc.close_websockets)

            def connect_emulator_btn_callback():
                gc.connect_websockets()
                return

if __name__ == "__main__":
    demo.launch()
