FIRST_FRAME_IMG_PROMPT = """\
Generate a 3D cartoon Pixar-style exaggerated character (full-body portrait) based on the provided image, both funny and romantic, with sparkling eyes, creating a playful and humorous atmosphere. Highly detailed, clean sharp line art, vibrant colors. Full-body standing portrait, width: 800px, height: 1200px, front-facing, looking at camera. The entire head and hair must be fully visible inside the frame, with generous space above the head to avoid cutting. Composition should be symmetrical and centered. Clear details preserved: original facial features, hairstyle, expression, body proportions, and clothing. Pure black background, no borders, no text.
"""

V_SPEECH_PROMPT = """\
It stands like a professional TV news anchor, completely still, with no movement in the shoulders, torso, or head. width: 800px, height: 1200px,Hands are raised in front of the chest, with minimal small gestures. Eyes look straight ahead, not sideways. Hands never go above the neck. It delivers the latest news quickly and fluently, with a natural expression, speaking at a fast and continuous pace, without any pauses.Video background in pure black.nagative:blur, distort, and low quality,Facial distortion
"""

V_THINK_PROMPT = """\
The character’s mouth does not speak or make any movements. The background remains pure black throughout. width: 800px, height: 1200px, When suddenly asked a difficult question, the character performs a thinking gesture, pauses briefly, and then gives the answer.nagative:blur, distort, and low quality,Facial distortion
"""

V_DEFAULT_PROMPT = """\
The character looks straight ahead, maintaining a slight, reserved smile, with a pure black background behind them.width: 800px, height: 1200px, nagative:blur, distort, and low quality,Facial distortion
"""

V_DANCE_IMAGE_PROMPT = """\
Replace the frog’s head and hands with the reference person’s portrait I provided. The target image should be high-definition, highly detailed, and seamlessly realistic, with no sense of discord. Width: 1000px, height: 1000px.
"""

V_DANCE_VIDEO_PROMPT = """\
A group of dancers performs in synchronized hip-hop poses, maintaining natural animal body proportions with realistic textures. Their full bodies are shown, dressed in stylish Korean streetwear designed to fit their forms, including modified loose street pants, cropped jackets, oversized hoodies, and sneakers on their feet. Accessories include baseball caps and necklaces. Their eyes convey the spirit of dancers, with natural hair shading and realistic beards. The dance movements are dynamic and full of energy. The scene takes place on a bustling urban street with graffiti walls and neon lights, rendered with cinematic depth of field and ultra-realistic photographic detail.Width: 1000px, height: 1000px.
nagative:blur, distort, and low quality,Facial distortion"""

V_SING_IMAGE_PROMPT = """\
Replace the rock character’s head in Image 2 with the portrait from Image 1 to generate a high-definition 3D image, width: 1000px, height: 1500px. The character’s face, hair, and expression should be rendered in high detail, with an exaggerated expression (referencing the expression in Image 2). The clothing should also be modified according to the character’s gender.Width: 800px, height: 1200px.
"""

V_SING_VIDEO_PROMPT = """\
He stands onstage roaring, muscles tensed, gripping a black Explorer guitar with lightning patterns etched into its body. His hair whips around under the searing white spotlights, partly obscuring his face. His eyes blaze with the righteous fury of thrash metal. His microphone stand is forged from twisted steel and broken stage rails, wrapped in colored electrical tape and guitar picks left from hundreds of battles. Behind him, an enormous wall of amps glows like a power plant—stacked Marshall heads spitting sparks from their edges. Flames lick the edge of the stage, while the crowd surges like an ocean of raised fists and devil horns. Atmosphere: it feels like a battlefield of sound. Pick-shaped lightning crackles in the air. The air is thick with smoke, sweat, and the scent of metal. Hetfield is captured mid-roar, mouth wide open, ready to unleash a verse that could shatter the earth.Width: 800px, height: 1200px.nagative:blur, distort, and low quality,Facial distortion"""