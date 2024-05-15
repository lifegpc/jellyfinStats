xgettext -D jellyfinstats __main__.py audio.py cache.py config.py utils.py \
    -L python -d jellyfinStats -p jellyfinstats/language --copyright-holder 'lifegpc' --package-name 'jellyfinStats' --package-version '1.0' --msgid-bugs-address 'root@lifegpc.com'
sed -i 's/charset=CHARSET/charset=UTF-8/g' jellyfinstats/language/jellyfinStats.po
msgmerge -U jellyfinstats/language/zh_CN/LC_MESSAGES/jellyfinStats.po jellyfinstats/language/jellyfinStats.po
