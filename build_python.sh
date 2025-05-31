pyinstaller                                 \
--onefile                                   \
--name evrmail                              \
--icon src/evrmail/gui/evrmail_tray_icon.png \
--add-data "src/evrmail/webui/dist:evrmail/webui/dist"       \
--add-data "src/evrmail/webui/public:evrmail/webui/public"   \
--add-data "src/evrmail/gui/icons:evrmail/gui/icons"        \
--add-data "example.evr.html:."             \
--add-data "config.json.example:."          \
evrmail_entry.py