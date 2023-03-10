import io,os,json,cv2,requests,asyncio,aiohttp,chat_exporter, numpy as np, pyzbar.pyzbar as pyzbar
import discord,discord.app_commands,discord.message
from discord import app_commands
from PIL import Image

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

def getConfig(key):
    with open("config.json", "r") as file:
        data = json.load(file)
        if key in data:
            return data[key]
        else:
            return False

def update_database(data, key):
    key = str(key)
    with open("database.json", "r") as file:
        json_data = json.load(file)
        json_data[key] = data[key]
    with open("database.json", "w") as file:
        json.dump(json_data, file)

def update_config(data, key):
    key = str(key)
    with open("config.json", "r") as file:
        json_data = json.load(file)
        json_data[key] = data[key]
    with open("config.json", "w") as file:
        json.dump(json_data, file)


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
    await tree.sync(guild=discord.Object(id=getConfig("serverID")))
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
        except FileNotFoundError:
            # the file doesn't exist, so create it
            update_database({f"{interaction.user.id}": str(barcodes[0].data)},f"{interaction.user.id}")
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
        
        if generateNewJSON == True:
            update_database({f"{interaction.user.id}": str(barcodes[0].data)},f"{interaction.user.id}")
        
        return barcodeData,imageFile
    else:
        print('Failed to download image from URL')
        return "FDI" # Fail to Download the Image

class manualVerificationButtonsFR(discord.ui.View): # French Language
    
    @discord.ui.button(label="Fermer le ticket", style=discord.ButtonStyle.primary, emoji="????", custom_id="close_ticket")
    async def close(self, interaction, button):

        more_permissions = []

        for member in interaction.channel.members:
            if interaction.channel.permissions_for(interaction.user) < interaction.guild.default_role.permissions:
                if member.guild_permissions.administrator or discord.utils.get(interaction.guild.roles, name="verification ticket team") in member.roles:
                    continue
                more_permissions.append(member)
        try:
            await interaction.channel.set_permissions(more_permissions[0], read_messages=False, connect=False)
        except IndexError:
            await interaction.response.send_message("???Erreur NRUP. Une erreur s'est produite lors de la recherche de l'utilisateur sur lequel supprimer l'autorisation.\nCette erreur est probablement due au fait que le ticket ??tait d??j?? ferm??.")
            return

        embedInstance=discord.Embed(title="V??rification manuelle ????", description=f"Ticket Ferm?? ???? Par {interaction.user.mention}\nQue voudriez-vous faire ensuite?")
        await interaction.response.send_message(embed=embedInstance, view=manualVerificationButtonsFR())


    @discord.ui.button(label="Obtenir la transcription", style=discord.ButtonStyle.primary, emoji="????", custom_id="get_transcript")
    async def transcript(self, interaction, button):
        
        if not (interaction.user.guild_permissions.administrator or discord.utils.get(interaction.guild.roles, name="verification ticket team") in interaction.user.roles):
            embedInstance=discord.Embed(title="V??rification manuelle ???? | Autorisations invalides", description=f"??? D??sol??, vous n'avez pas assez de permissions pour utiliser ceci.")
            await interaction.response.send_message(embed=embedInstance, view=manualVerificationButtonsFR())
            return
        
        await chat_exporter.quick_export(interaction.channel)

        embedInstance=discord.Embed(title="V??rification manuelle ????", description=f"Transcription sauvegard??e en tant que fichier HTML. ????\nQue voulez-vous faire ensuite ??")
        await interaction.response.send_message(embed=embedInstance, view=manualVerificationButtonsFR())
    @discord.ui.button(label="Supprimer la cha??ne", style=discord.ButtonStyle.primary, emoji="???", custom_id="del_channel")
    async def delchanel(self, interaction, button):

        if not (interaction.user.guild_permissions.administrator or discord.utils.get(interaction.guild.roles, name="verification ticket team") in interaction.user.roles):
            embedInstance=discord.Embed(title="V??rification manuelle ???? | Autorisations invalides", description=f"??? D??sol??, vous n'avez pas assez de permissions pour utiliser ceci.")
            await interaction.response.send_message(embed=embedInstance, view=manualVerificationButtonsFR())
            return
        
        channel = client.get_channel(interaction.channel.id)

        embedInstance=discord.Embed(title="V??rification manuelle ????", description=f"Suppression du ticket en cours...")
        await interaction.response.send_message(embed=embedInstance)

        await asyncio.sleep(1)

        await channel.delete()
class manualVerificationButtonsEN(discord.ui.View): # English Lanuage

    @discord.ui.button(label="Close ticket", style=discord.ButtonStyle.primary, emoji="????", custom_id="close_ticket")
    async def close(self, interaction, button):

        more_permissions = []

        for member in interaction.channel.members:
            if interaction.channel.permissions_for(interaction.user) < interaction.guild.default_role.permissions:
                if member.guild_permissions.administrator or discord.utils.get(interaction.guild.roles, name="verification ticket team") in member.roles:
                    continue
                more_permissions.append(member)
        try:
            await interaction.channel.set_permissions(more_permissions[0], read_messages=False, connect=False)
        except IndexError:
            await interaction.response.send_message("??? Error NRUP. Had an error while finding User to remove permission to.\nThis error is most likely caused because the ticket was allready closed.")
            return

        embedInstance=discord.Embed(title="Manual Verification ????", description=f"Ticket Closed ???? By {interaction.user.mention}\nWhat would you like to do next?")
        await interaction.response.send_message(embed=embedInstance, view=manualVerificationButtonsEn())


    @discord.ui.button(label="Get Transcript", style=discord.ButtonStyle.primary, emoji="????", custom_id="get_transcript")
    async def transcript(self, interaction, button):
        
        if not (interaction.user.guild_permissions.administrator or discord.utils.get(interaction.guild.roles, name="verification ticket team") in interaction.user.roles):
            embedInstance=discord.Embed(title="Manual Verification ???? | Invalid Permissions", description=f"??? Sorry you do not have enough permissions to use this.")
            await interaction.response.send_message(embed=embedInstance, view=manualVerificationButtonsEn())
            return
        
        await chat_exporter.quick_export(interaction.channel)

        embedInstance=discord.Embed(title="Manual Verification ????", description=f"Transcript Saved as HTML File. ????\nWhat would you like to do next?")
        await interaction.response.send_message(embed=embedInstance, view=manualVerificationButtonsEn())
    @discord.ui.button(label="Delete Channel", style=discord.ButtonStyle.primary, emoji="???", custom_id="del_channel")
    async def delchanel(self, interaction, button):

        if not (interaction.user.guild_permissions.administrator or discord.utils.get(interaction.guild.roles, name="verification ticket team") in interaction.user.roles):
            embedInstance=discord.Embed(title="Manual Verification ???? | Invalid Permissions", description=f"??? Sorry you do not have enough permissions to use this.")
            await interaction.response.send_message(embed=embedInstance, view=manualVerificationButtonsEn())
            return
        
        channel = client.get_channel(interaction.channel.id)

        embedInstance=discord.Embed(title="Manual Verification ????", description=f"Deleting Ticket...")
        await interaction.response.send_message(embed=embedInstance)

        await asyncio.sleep(1)

        await channel.delete()

class verificationButtonsFR(discord.ui.View): # French Language
    @discord.ui.button(label="V??rifier!", style=discord.ButtonStyle.primary, emoji="<:acceptmc:974132622240403476>", custom_id="verify_auto") # Create a button with the label "???? Click me!" with color Blurple
    async def verify(self, interaction, button):
        await interaction.response.send_message("Veuillez envoyer une image de votre **carte d'identit??** ici (expire dans 2 minutes)") # Send a message when the button is clicked
        
        def check(m):
            if m.channel.id == interaction.channel.id and interaction.user.id == m.author.id:
                return True
            return False
        
        try:
            msg = await client.wait_for('message', check=check, timeout=120)
        except asyncio.TimeoutError:
            await interaction.channel.send('D??sol??, vous n\'avez pas r??pondu dans le d??lai de 2 minutes, r??essayez avec la commande /verify :)')
        else:

            if len(msg.attachments) > 0:
                image = msg.attachments[0]
                if str.lower(image.filename).endswith('.png') or str.lower(image.filename).endswith('.jpg') or str.lower(image.filename).endswith('.jpeg'):
                    
                    embed=discord.Embed(title="Veuillez patienter...", description="votre carte d'identit?? est en cours de v??rification...")
                    await interaction.channel.send(embed=embed)

                    barcode = read_barcode_from_url(image.url,interaction)
                    
                    # turn PIL image to png

                    if barcode == "FDI":
                        await interaction.channel.send("??? D??sol??, nous n'avons pas pu charger votre image discord, le serveur discord cnd est peut-??tre en panne...\n En savoir plus : https://discordstatus.com/ Erreur : FDI")
                    elif barcode == "LZF":
                        await interaction.channel.send("??? D??sol??, nous n'avons pas pu scanner votre carte d'identit??, veuillez prendre une photo dans un endroit bien ??clair?? et r??essayer\nErreur: LZF")
                    elif barcode == "UAR":
                        await interaction.channel.send(f"??? D??sol??, nous avons d??j?? enregistr?? votre carte d'identit?? dans la base de donn??es de v??rification\nErreur: UAR")
                    elif barcode == "ISC":
                        await interaction.channel.send("??? D??sol??, nous avons trouv?? votre carte d'identit?? comme ??tant une carte frauduleuse, si vous n'??tes pas d'accord, vous pouvez obtenir une v??rification manuelle\nErreur:ISC")
                    else:
                        await interaction.channel.send("??? Succ??s! vous serez bient??t v??rifi?? :)")
                        await imageThing(image.url,interaction)
                else:
                    await interaction.channel.send(f"??? D??sol??, `{getContentType(image.url)[1]}` n'est pas un type d'extension pris en charge :(")
            else:
                await interaction.channel.send("??? D??sol??, ce n'est pas une image, pour refaire la v??rification, tapez ?? nouveau la commande `/verify` pour r??essayer :D")
    @discord.ui.button(label="V??rification manuelle", style=discord.ButtonStyle.danger, emoji="????", custom_id="v??rifier_manuel") # Cr??er un bouton avec le libell?? "???? Cliquez sur moi!" avec la couleur Blurple
    async def verify_manual(self, interaction, button):
        embedInstance=discord.Embed(title="V??rification manuelle ????", description="G??n??ration d'un nouveau Ticket...")
        message = await interaction.response.send_message(embed=embedInstance, ephemeral=True)
        # cr??er la cat??gorie et le canal
        verification_category = next((category for category in interaction.guild.categories if category.name == "Manual Verification Tickets"), None)
        
        if not verification_category:
            verification_category = await interaction.guild.create_category("Manual Verification Tickets")
            await verification_category.set_permissions(interaction.guild.default_role, read_messages=False)

        verifcationChat = await interaction.guild.create_text_channel(f"ticket-{len([channel for channel in interaction.guild.text_channels if channel.category == verification_category]) + 1}", category=verification_category)
        await verifcationChat.set_permissions(interaction.user, read_messages=True, connect=False)
        
        embedInstance=discord.Embed(title="V??rification manuelle ????", description=f"fait! le ticket a ??t?? cr????. <#{verifcationChat.id}>")
        await interaction.edit_original_response(embed=embedInstance)

        embedInstance=discord.Embed(title="V??rification manuelle ????", description=f"veuillez patienter notre ??quipe de v??rification manuelle va arriver dans un moment.")
        await verifcationChat.send(embed=embedInstance, view=manualVerificationButtonsFR())
class verificationButtonsEN(discord.ui.View): # English Language
    @discord.ui.button(label="Verify!", style=discord.ButtonStyle.primary, emoji="<:acceptmc:974132622240403476>", custom_id="verify_auto") # Create a button with the label "???? Click me!" with color Blurple
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
                        await interaction.channel.send("??? Sorry we coudn't load your discord image, discord cnd might be down...\n Learn More: https://discordstatus.com/ Error: FDI")
                    elif barcode == "LZF":
                        await interaction.channel.send("??? Sorry we coudn't scan your identity card, please take a picture in a well lit room and try again\nError: LZF")
                    elif barcode == "UAR":
                        await interaction.channel.send(f"??? Sorry we found your id allready registered in the verification database\nError: UAR")
                    elif barcode == "ISC":
                        await interaction.channel.send("??? Sorry we found your id card as a fraudulent card, if you don't agree you can get manual verification\nError:ISC")
                    else:
                        
                        
                        await interaction.channel.send("??? Success! you will be verified soon :)")
                        await imageThing(image.url,interaction)
                        
                else:
                    await interaction.channel.send(f"??? Sorry `{getContentType(image.url)[1]}` is not a supported extention type unfortunataly :(")
            else:
                await interaction.channel.send("??? Sorry that's not an image, to redo verification retype the `/verify` command to try again :D")

                
                        
        
    
    @discord.ui.button(label="Manual Verification", style=discord.ButtonStyle.danger, emoji="????", custom_id="verify_manual") # Create a button with the label "???? Click me!" with color Blurple
    async def verify_manual(self, interaction, button):
        embedInstance=discord.Embed(title="Manual Verification ????", description="Generating new ticket...")
        message = await interaction.response.send_message(embed=embedInstance, ephemeral=True)
        
        # create category and channel
        verification_category = next((category for category in interaction.guild.categories if category.name == "Manual Verification Tickets"), None)
        
        if not verification_category:
            verification_category = await interaction.guild.create_category("Manual Verification Tickets")
            await verification_category.set_permissions(interaction.guild.default_role, read_messages=False)

        verifcationChat = await interaction.guild.create_text_channel(f"ticket-{len([channel for channel in interaction.guild.text_channels if channel.category == verification_category]) + 1}", category=verification_category)
        await verifcationChat.set_permissions(interaction.user, read_messages=True, connect=False)
        
        embedInstance=discord.Embed(title="Manual Verification ????", description=f"done! ticket has been made. <#{verifcationChat.id}>")
        await interaction.edit_original_response(embed=embedInstance)

        embedInstance=discord.Embed(title="Manual Verification ????", description=f"please wait patiently our manual verification team is going to be here in a moment.")
        await verifcationChat.send(embed=embedInstance, view=manualVerificationButtonsEN())

class languageSelectButtons(discord.ui.View): # Lanuage Selector

    @discord.ui.button(label="French / Fran??ais", style=discord.ButtonStyle.primary, emoji="????????", custom_id="fr_lang")
    async def french(self, interaction, button):
        update_database({f"{interaction.user.id}-language":"FR"},f"{interaction.user.id}-language")
        await interaction.response.send_message("Pr??f??rence mise ?? jour")
    
    @discord.ui.button(label="English / Anglais", style=discord.ButtonStyle.primary, emoji="????????", custom_id="en_lang")
    async def english(self, interaction, button):
        update_database({f"{interaction.user.id}-language":"EN"},f"{interaction.user.id}-language")
        await interaction.response.send_message("Preference updated")


@tree.command(name="languageselector", description="Select a language of your choice | Selectionez une langue de votre choix",guild=discord.Object(id=getConfig("serverID"))) #Add the guild ids in which the slash command will appear. If it should be in all, remove the argument, but note that it will take some time (up to an hour) to register the command if it's for all guilds.
async def languageselector(interaction):
    embed=discord.Embed(title="Language selector / S??lecteur de langue ????", description="Please select your language of choice.\nVeuillez s??lectionner la langue de votre choix.")
    await interaction.response.send_message(embed=embed, view=languageSelectButtons())

def getLanguage(interaction):
    with open("database.json", "r") as file:
        data = json.load(file)

        if f"{interaction.user.id}-language" in data:
            return data[f"{interaction.user.id}-language"]
        else:
            return False

@tree.command(name="verify", description="Verifies you :)",guild=discord.Object(id=getConfig("serverID"))) #Add the guild ids in which the slash command will appear. If it should be in all, remove the argument, but note that it will take some time (up to an hour) to register the command if it's for all guilds.
async def verify(interaction):

    

    language = NotImplemented
    with open("database.json", "r") as file:
        data = json.load(file)

        if f"{interaction.user.id}-language" in data:
            language = data[f"{interaction.user.id}-language"]
        else:
            language = "null"

    if not (interaction.channel.id == getConfig('channelVerID')):
        if language == "EN":
            await interaction.response.send_message("Im sorry but you can't use this command here")
            return
        elif language == "FR":
            await interaction.response.send_message("Je suis d??sol?? mais vous ne pouvez pas utiliser cette commande ici.")
            return

    
    if language == "EN":
        
        embed=discord.Embed(title="Verify ???", description=f"To verify yourself as a legitimate person that comes from {getConfig('serverName')}, please verify yourself by taking a picture of your identification card.")
        embed.add_field(name="Wait but how should i be verifying?", value="You need to take a picture of your id card and send it into this channel, by doing so the bot will search into the database to verify its you", inline=True)
        embed.add_field(name="Can i do this for multiple accounts?", value="Unfortunately not, if you really need multiple accounts or your other account that was on the server either got terminated or disabled, you can ask for manual verification.", inline=True)
        embed.set_footer(text=f"*by pressing verify you are agreeing that our server can store your {getConfig('serverName')} id card image*")
        await interaction.response.send_message(embed=embed, view=verificationButtonsEN())
    elif language == "FR":
        embed=discord.Embed(title="V??rifier ???", description=f"Pour vous v??rifier en tant que personne l??gitime qui vient de {getConfig('serverName')}, veuillez vous v??rifier en prenant une photo de votre carte d'identit??.")
        embed.add_field(name="Mais comment dois-je v??rifier?", value="Vous devez prendre une photo de votre carte d'identit?? et la envoyer dans ce canal, en le faisant, le bot cherchera dans la base de donn??es pour v??rifier que c'est vous", inline=True)
        embed.add_field(name="Puis-je le faire pour plusieurs comptes?", value="Malheureusement non, si vous avez vraiment besoin de plusieurs comptes ou si votre autre compte qui ??tait sur le serveur a ??t?? soit termin?? ou d??sactiv??, vous pouvez demander une v??rification manuelle.", inline=True)
        embed.set_footer(text=f"*en appuyant sur v??rifier, vous acceptez que notre serveur puisse stocker votre image de carte d'identit?? de {getConfig('serverName')}*")
        await interaction.response.send_message(embed=embed, view=verificationButtonsFR())
    else:
        embed=discord.Embed(title="Language selector / S??lecteur de langue ????", description="Please select your language of choice.\nVeuillez s??lectionner la langue de votre choix.")
        await interaction.response.send_message(embed=embed, view=languageSelectButtons())

client.run(getConfig('token'))
