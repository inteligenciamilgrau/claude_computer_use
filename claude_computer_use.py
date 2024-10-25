import anthropic
import mss
import base64
import io
from dotenv import load_dotenv
import mss.tools
from PIL import Image
load_dotenv()

monitor_escolhido = 2
monitor_offset = [1920, 0]

client = anthropic.Anthropic()

messages = []

def perguntando(messages):
    response = client.beta.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        tools=[
            {
            "type": "computer_20241022",
            "name": "computer",
            "display_width_px": 1024,
            "display_height_px": 768,
            "display_number": 1,
            },
        ],
        messages=messages,
        betas=["computer-use-2024-10-22"],
    )
    #print(response)
    return response

def grab_screen_of_monitor(monitor_index=1):
    with mss.mss() as sct:
        # Get the information of all monitors connected
        monitors = sct.monitors

        # Check if the specified monitor index is valid
        if monitor_index < 1 or monitor_index >= len(monitors):
            raise ValueError(f"Invalid monitor index: {monitor_index}. Available monitors: 1 to {len(monitors) - 1}")

        # Select the monitor based on the provided index
        monitor = monitors[monitor_index]

        # Capture the screen of the specified monitor
        screenshot = sct.grab(monitor)

        # Convert the screenshot to a JPEG image in memory
        img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
        img = img.resize((1024, 768))

        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG')
        img_buffer.seek(0)

        # Encode the image as base64
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

        return img_base64


chat_on = True
todas_messages = []

while chat_on:
    pergunta = input("O que quer fazer? (sair 'x'): ")

    if pergunta.lower() == "x":
        break

    todas_messages.append({"role": "user", "content": pergunta})

    resposta = perguntando(todas_messages)

    print("Resposta:", resposta.content[0].text, "\n")
    todas_messages.append({"role": "assistant", "content": resposta.content})

    while resposta.stop_reason == "tool_use":
        print("Próxima ação:", resposta.content[1].input['action'], "\n")
        if 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "screenshot":
            image_base64 = grab_screen_of_monitor(monitor_escolhido)
            pergunta_tool = {
                    "role": "user",
                    "content": [{
                        "tool_use_id": resposta.content[1].id,
                        "type": "tool_result"},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_base64,
                            }
                        }
                    ]
                }
            todas_messages.append(pergunta_tool)

            resposta = perguntando(todas_messages)
            print("Resposta SCREENSHOT:", resposta.content[0].text, "\n")
            
            
        elif 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "mouse_move":
            import pyautogui

            def convert_coordinate(old_resolution, new_resolution, point):
                old_width, old_height = old_resolution
                new_width, new_height = new_resolution
                x, y = point

                new_x = x * new_width / old_width
                new_y = y * new_height / old_height

                return [int(new_x), int(new_y)]

            new_coordinate = convert_coordinate((1024, 768), (1920, 1080), resposta.content[1].input['coordinate'])
            
            if monitor_escolhido == 2:
                new_coordinate[0] = new_coordinate[0] + monitor_offset[0]
                pyautogui.moveTo(new_coordinate)
            else:
                pyautogui.moveTo(new_coordinate)
            pergunta_tool = {
                    "role": "user",
                    "content": [{
                        "tool_use_id": resposta.content[1].id,
                        "type": "tool_result"},
                        {
                            "type": "text",
                            "text": "Mouse movido"
                        }
                    ]
                }
            todas_messages.append(pergunta_tool)

            resposta = perguntando(todas_messages)
            print("Resposta MOVE:", resposta.content[0].text, "\n")
        elif 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "left_click":
            import pyautogui

            pyautogui.click()
            pergunta_tool = {
                    "role": "user",
                    "content": [{
                        "tool_use_id": resposta.content[1].id,
                        "type": "tool_result"},
                        {
                            "type": "text",
                            "text": "Clicado"
                        }
                    ]
                }
            todas_messages.append(pergunta_tool)

            resposta = perguntando(todas_messages)
            print("Resposta Click:", resposta.content[0].text, "\n")
        elif 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "type":
            print("TYPE")
            break
        elif 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "key":
            print("KEY")
            break
        elif 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "left_click_drag":
            print("LEFT CLICK DRAG")
            break
        elif 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "right_click":
            print("RIGHT_CLICK")
            break
        elif 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "middle_click":
            print("MIDDLE CLICK")
            break
        elif 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "double_click":
            print("DOUBLE CLICK")
            break
        elif 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "cursor_position":
            print("CURSOR POSITION")
            break
        todas_messages.append({"role": "assistant", "content": resposta.content})
