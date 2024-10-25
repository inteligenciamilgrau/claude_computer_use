import anthropic
import mss
import base64
import io
from dotenv import load_dotenv
import mss.tools
import pyautogui
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

def template_resposta_tool(mensagem, id):
    return {
        "role": "user",
        "content": [{
            "tool_use_id": id,
            "type": "tool_result"},
            {
                "type": "text",
                "text": mensagem
            }
        ]
    }

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
            pergunta_tool = template_resposta_tool("Mouse Movido", resposta.content[1].id)
            todas_messages.append(pergunta_tool)

            resposta = perguntando(todas_messages)
            print("Resposta MOVE:", resposta.content[0].text, "\n")
        elif 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "left_click":
            pyautogui.click(button='left')
            pergunta_tool = template_resposta_tool("Clique esquerdo realizado", resposta.content[1].id)
            todas_messages.append(pergunta_tool)

            resposta = perguntando(todas_messages)
            print("Resposta Left Click:", resposta.content[0].text, "\n")
        elif 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "type":
            pyautogui.write(resposta.content[1].input['text'])
            pergunta_tool = template_resposta_tool("Texto escrito", resposta.content[1].id)
            todas_messages.append(pergunta_tool)

            resposta = perguntando(todas_messages)
            print("Resposta Type:", resposta.content[0].text, "\n")
        elif 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "key":
            #* `key`: Press a key or key-combination on the keyboard.
            #      - This supports xdotool's `key` syntax.
            #      - Examples: "a", "Return", "alt+Tab", "ctrl+s", "Up", "KP_0" (for the numpad 0 key).
            #    * 
            if resposta.content[1].input['text'] == "Return":
                pyautogui.press("return")
                pergunta_tool = template_resposta_tool("Apertado " + resposta.content[1].input['text'], resposta.content[1].id)
                todas_messages.append(pergunta_tool)

                resposta = perguntando(todas_messages)
                print("Resposta Type:", resposta.content[0].text, "\n")
            else:
                print("Falta implementar na ação 'key' o comando:", resposta.content[1].input['text'], "\n")
                break
            
        elif 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "left_click_drag":
            def left_click_drag(x, y):
                pyautogui.mouseDown(button='left')
                
                # Arrasta o cursor até a posição final
                pyautogui.moveTo(x, y, duration=0.5)  # duration pode ser ajustado para controlar a velocidade
                
                # Solta o botão do mouse
                pyautogui.mouseUp(button='left')
            coord = resposta.content[1].input['coordinate']
            left_click_drag(coord[0], coord[1])

            pergunta_tool = template_resposta_tool("Clique esquerdo e arrasta realizado", resposta.content[1].id)
            todas_messages.append(pergunta_tool)

            resposta = perguntando(todas_messages)
            print("Resposta Left Click Drag:", resposta.content[0].text, "\n")
        elif 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "right_click":
            pyautogui.click(button='right')
            pergunta_tool = template_resposta_tool("Clique direito realizado", resposta.content[1].id)
            todas_messages.append(pergunta_tool)

            resposta = perguntando(todas_messages)
            print("Resposta Right Click:", resposta.content[0].text, "\n")
        elif 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "middle_click":
            pyautogui.click(button='middle')
            pergunta_tool = template_resposta_tool("Clique do meio realizado", resposta.content[1].id)
            todas_messages.append(pergunta_tool)

            resposta = perguntando(todas_messages)
            print("Resposta Middle Click:", resposta.content[0].text, "\n")
        elif 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "double_click":
            pyautogui.doubleClick()
            pergunta_tool = template_resposta_tool("Clique esquerdo duplo realizado", resposta.content[1].id)
            todas_messages.append(pergunta_tool)

            resposta = perguntando(todas_messages)
            print("Resposta Double Click:", resposta.content[0].text, "\n")
        elif 'action' in resposta.content[1].input and resposta.content[1].input['action'] == "cursor_position":
            x, y = pyautogui.position()
            pergunta_tool = template_resposta_tool(f"Posição do mouse: x={x}, y={y}", resposta.content[1].id)
            todas_messages.append(pergunta_tool)

            resposta = perguntando(todas_messages)
            print("Resposta Double Click:", resposta.content[0].text, "\n")
        todas_messages.append({"role": "assistant", "content": resposta.content})
