pyinstaller                                 \
--onefile                                   \
--name evrmail                              \
--add-data "src/evrmail/webui/dist:evrmail/webui/dist"       \
--add-data "src/evrmail/webui/public:evrmail/webui/public"   \
--add-data "example.evr.html:."             \
--add-data "config.json.example:."          \
evrmail_entry.py