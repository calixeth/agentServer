FIRST_FRAME_IMG_PROMPT = """\
Generate a 3D cartoon Pixar-style exaggerated character (full-body portrait) based on the provided image, both funny and romantic, with sparkling eyes, creating a playful and humorous atmosphere. Highly detailed, clean sharp line art, vibrant colors. Full-body standing portrait, width: 1024px, height: 1536px, front-facing, looking at camera. The entire head and hair must be fully visible inside the frame, with generous space above the head to avoid cutting. Composition should be symmetrical and centered. Clear details preserved: original facial features, hairstyle, expression, body proportions, and clothing. Pure black background, no borders, no text.
"""

V_SPEECH_PROMPT = """\
It stands like a professional TV news anchor, completely still, with no movement in the shoulders, torso, or head. width: 1024px, height: 1536px,Hands are raised in front of the chest, with minimal small gestures. Eyes look straight ahead, not sideways. Hands never go above the neck. It delivers the latest news quickly and fluently, with a natural expression, speaking at a fast and continuous pace, without any pauses.Video background in pure black.nagative:blur, distort, and low quality
"""

V_THINK_PROMPT = """\
The character’s mouth does not speak or make any movements. The background remains pure black throughout. width: 1024px, height: 1536px, When suddenly asked a difficult question, the character performs a thinking gesture, pauses briefly, and then gives the answer.nagative:blur, distort, and low quality
"""

V_TURN_PROMPT = """\
It turns to the right in a full 360-degree spin, then returns to face the camera, with minimal movement range. width: 1024px, height: 1536px, Video background in pure black.nagative:blur, distort, and low quality
"""

V_DEFAULT_PROMPT = """\
The character looks straight ahead, maintaining a slight, reserved smile, with a pure black background behind them. width: 1024px, height: 1536px, nagative:blur, distort, and low quality
"""

V_DANCE_IMAGE_PROMPT = """\
The frog dancing image is the base image. Generate the target image by replacing the frog’s head and hands in the base image with the reference person’s portrait I provided. The target image should be high-definition, highly detailed, seamlessly realistic, and with no sense of discord. At the same time, expand the generated image to the size: width 1024px, height 1536px.
"""

V_DANCE_VIDEO_PROMPT = """\
A group of dancers performs in synchronized hip-hop poses, maintaining natural animal body proportions with realistic textures. Their full bodies are shown, dressed in stylish Korean streetwear designed to fit their forms, including modified loose street pants, cropped jackets, oversized hoodies, and sneakers on their feet. Accessories include baseball caps and necklaces. Their eyes convey the spirit of dancers, with natural hair shading and realistic beards. The dance movements are dynamic and full of energy. The scene takes place on a bustling urban street with graffiti walls and neon lights, rendered with cinematic depth of field and ultra-realistic photographic detail. The final image size should be 1536px wide and 1024px high.nagative:blur, distort, and low quality"""

V_SING_IMAGE_PROMPT = """\
Replace the rock character’s head in Image 2 with the portrait from Image 1 to generate a high-definition 3D image. Leave 20% space between the top of the character’s head and the edge of the photo. The character’s face, hair, and expression should be rendered in high detail, with an exaggerated expression (referencing the expression in Image 2). The clothing should also be modified according to the character’s gender. The final image size should be 1024px wide and 1536px high.Style: 3D cartoon / exaggerated caricature + mixed with realistic PBR materials.  Mood: Funny yet hardcore, with a heavy metal stage vibe. The character is designed as a comedic figure, but the lighting and materials pursue a “real stage” texture.  
"""

V_SING_VIDEO_PROMPT = """\
He stands onstage roaring, muscles tensed, gripping a black Explorer guitar with lightning patterns etched into its body. His hair whips around under the searing white spotlights, partly obscuring his face. His eyes blaze with the righteous fury of thrash metal. His microphone stand is forged from twisted steel and broken stage rails, wrapped in colored electrical tape and guitar picks left from hundreds of battles. Behind him, an enormous wall of amps glows like a power plant—stacked Marshall heads spitting sparks from their edges. Flames lick the edge of the stage, while the crowd surges like an ocean of raised fists and devil horns. Atmosphere: it feels like a battlefield of sound. Pick-shaped lightning crackles in the air. The air is thick with smoke, sweat, and the scent of metal. Hetfield is captured mid-roar, mouth wide open, ready to unleash a verse that could shatter the earth.The final video size should be 1024px wide and 1536px high.nagative:blur, distort, and low quality"""

V_FIGURE_IMAGE_PROMPT="""\
Use the nano-banana model to create a 1/7 scale commercialized figure of thecharacter in the illustration, in a realistic styie and environment.Place the figure on a computer desk, using a circular transparent acrylic base without any text.On the computer screen, display the ZBrush modeling process of the figure.Next to the computer screen, place a BANDAl-style toy packaging box printedwith the original artwork.The final image size should be 1536px wide and 1024px high.
"""

V_FIGURE_VIDEO_PROMPT="""\
A hand slowly picks up the figurine from the desk and carefully turns it over to examine the details.
"""