# Barcode Verification Discord Bot
this bot is built using [discord.py](https://pypi.org/project/discord.py/) and utilizes the [pyzbar](https://pypi.org/project/pyzbar/) library to scan barcodes. This bot allows users to verify using a barcode and saves the content and the image in a directory for future reference. However configuring it will be hard if you do not know how to interperet code. I also used **ChatGPT** to help me a bit so thats why there are a lot of comments .-.

### Building the project
first you need to clone the project so type in cmd:
```
git clone https://github.com/notpoiu/barcodeverificationbot
```
then open up the folder in command prompt:
`C:\Users\Admin\Desktop> cd bar `

then install the requirements by typing this:
```
pip install -r requirements.txt
```
then change the token and change the guild ids of the slash commands and tweak the project to your liking :)
and to run it type: `python bot.py`

### Todo list:

 - [x] ID card image downloader
 - [x] ID card content and barcode type saver in json database 
 - [x] Make the bot robust
 - [ ] Configuration file to make it easier to configure :o
