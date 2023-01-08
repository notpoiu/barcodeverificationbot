import discord
from discord import app_commands
import io,os,json,cv2,requests,asyncio,aiohttp
import discord.message
from PIL import Image
import pyzbar.pyzbar as pyzbar
import numpy as np


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)



def getContentType(pageUrl):
    file_name, file_ext = os.path.splitext(os.path.basename(pageUrl))
    return file_name,file_ext

async def imageThing(url,interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            image_data = await resp.read()
            imageFile = Image.open(io.BytesIO(image_data))
            file_path = os.path.join("barcodes\\", f"{interaction.user.id}.png")
            imageFile.save(file_path,format="PNG")
            return True

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=998277664290897921))
    print(f'We have logged in as {client.user}')

def read_barcode_from_url(url,interaction):
    # Download the image
    response = requests.get(url, allow_redirects=False)

    # Check that the image was successfully downloaded
    if response.status_code == 200:
        # Convert the image to a PIL Image object
        barcodeImg = cv2.cvtColor(np.array(Image.open(io.BytesIO(requests.get(url).content))), cv2.COLOR_RGB2BGR)
        barcodes = pyzbar.decode(barcodeImg)
        
        generateNewJSON = True
        
        # Scan the image for barcodes
        
        imageFile = NotImplemented

        if len(barcodes) == 0:
            return "LZF" # Length Zero Fail

        dataBarcodeFilter = str(barcodes[0].data).replace("'","")
        dataBarcodeFilter = dataBarcodeFilter.replace("b","")

        if int(dataBarcodeFilter) < 4000000 or barcodes[0].type != "CODE39":
            return "ISC" # INVALID SCAN CARD

        try:
            with open("database.json", "r") as f:
                # read the data from the file as JSON
                data = json.load(f)
                if str(barcodes[0].data) in data.values():
                    return "UAR" # User Allready Registered
                else:
                    generateNewJSON = True
        except FileNotFoundError:
            # the file doesn't exist, so create it
            with open("database.json", "w") as f:
                # write an empty dictionary to the file
                dictionairy = {interaction.user.id: str(barcodes[0].data)}
                json.dump(dictionairy, f)
                generateNewJSON = False
        
        #imageThing()
        
        
        # Print the data from each barcode found
        for barcode in barcodes:
            (x, y, w, h) = barcode.rect

            cv2.rectangle(barcodeImg, (x-10, y-10),
                          (x + w+10, y + h+10),
                          (255, 0, 0), 2)

        

        barcodeData = []
        index = 0
        for barcode in barcodes:
            barcodeData.insert(index, barcode.data)
            index += 1
        
        if generateNewJSON:
            database = {}
            with open("database.json", "r") as f:
                    # read the data from the file as JSON
                    database = json.load(f)
            
            with open("database.json", "w") as f:
                    # read the data from the file as JSON
                    database.update({f"{interaction.user.id}": str(barcodes[0].data)})
                    json.dump(database,f)

        return barcodeData,imageFile
    else:
        print('Failed to download image from URL')
        return "FDI" # Fail to Download the Image

9

class verificationButtonsEN(discord.ui.View): # Create a class called MyView that subclasses discord.ui.View
    @discord.ui.button(label="Verify!", style=discord.ButtonStyle.primary, emoji="<:acceptmc:974132622240403476>", custom_id="verify_auto") # Create a button with the label "😎 Click me!" with color Blurple
    async def verify(self, interaction, button):
        await interaction.response.send_message("Please send an image of your **id card** here *(expiring in 2 minutes)*") # Send a message when the button is clicked

        def check(m):
            if m.channel.id == interaction.channel.id and interaction.user.id == m.author.id:
                return True
            return False
        
        try:
            msg = await client.wait_for('message', check=check, timeout=120)
        except asyncio.TimeoutError:
            await interaction.channel.send('Sorry you did not respond in the 2 minute time limit try again to do /verify :)')
        else:

            if len(msg.attachments) > 0:
                image = msg.attachments[0]
                if str.lower(image.filename).endswith('.png') or str.lower(image.filename).endswith('.jpg') or str.lower(image.filename).endswith('.jpeg'):
                    
                    embed=discord.Embed(title="Please wait...", description="your id is going through a verification step and is being processed by the machine...")
                    await interaction.channel.send(embed=embed)

                    barcode = read_barcode_from_url(image.url,interaction)
                    
                    # turn PIL image to png

                    if barcode == "FDI":
                        await interaction.channel.send("❌ Sorry we coudn't load your discord image, discord cnd might be down...\n Learn More: https://discordstatus.com/ Error: FDI")
                    elif barcode == "LZF":
                        await interaction.channel.send("❌ Sorry we coudn't scan your identity card, please take a picture in a well lit room and try again\nError: LZF")
                    elif barcode == "UAR":
                        await interaction.channel.send(f"❌ Sorry we found your id allready registered in the verification database\nError: UAR")
                    elif barcode == "ISC":
                        await interaction.channel.send("❌ Sorry we found your id card as a fraudulent card, if you don't agree you can get manual verification\nError:ISC")
                    else:
                        
                        
                        await interaction.channel.send("✔ Success! you will be verified soon :)")
                        await imageThing(image.url,interaction)
                        
                else:
                    await interaction.channel.send(f"❌ Sorry `{getContentType(image.url)[1]}` is not a supported extention type unfortunataly :(")
            else:
                await interaction.channel.send("❌ Sorry that's not an image, to redo verification retype the `/verify` command to try again :D")

                
                        
        
    
    @discord.ui.button(label="Manual Verification", style=discord.ButtonStyle.danger, emoji="📋", custom_id="verify_manual") # Create a button with the label "😎 Click me!" with color Blurple
    async def verify_manual(self, interaction, button):
        await interaction.response.send_message("You clicked the button!") # Send a message when the button is clicked


@tree.command(name="verify", description="Verifies you :)",guild=discord.Object(id=998277664290897921)) #Add the guild ids in which the slash command will appear. If it should be in all, remove the argument, but note that it will take some time (up to an hour) to register the command if it's for all guilds.
async def verify(interaction): 
    embed=discord.Embed(title="Verify ✅", description="To verify yourself as a legitimate person that comes from **X**, please verify yourself by taking a picture of your identification card.")
    embed.add_field(name="Wait but how should i be verifying?", value="You need to take a picture of your id card and send it into this channel, by doing so the bot will search into the database to verify its you", inline=True)
    embed.add_field(name="Can i do this for multiple accounts?", value="Unfortunately not, if you really need multiple accounts or your other account that was on the server either got terminated or disabled, you can ask for manual verification.", inline=True)
    embed.set_footer(text="*by pressing verify you are agreeing that our server can store your id card image*")
    await interaction.response.send_message(embed=embed, view=verificationButtonsEN())

client.run()
