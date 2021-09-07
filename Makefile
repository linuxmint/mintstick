install:
	mkdir -p $(DESTDIR)/usr/lib/mintstick
	install -m0755 lib/*.py $(DESTDIR)/usr/lib/mintstick
	mkdir -p $(DESTDIR)/usr/share/mintstick
	cp share/mintstick/* $(DESTDIR)/usr/share/mintstick
	mkdir -p $(DESTDIR)/usr/share/applications
	cp share/applications/* $(DESTDIR)/usr/share/applications
	mkdir -p $(DESTDIR)/usr/share/polkit-1/actions
	cp share/polkit/* $(DESTDIR)/usr/share/polkit-1/actions
	mkdir -p $(DESTDIR)/usr/bin
	install -m0755 mintstick $(DESTDIR)/usr/bin
	mkdir -p $(DESTDIR)/usr/share/nemo/actions
	cp share/nemo/actions/* $(DESTDIR)/usr/share/nemo/actions
	mkdir -p $(DESTDIR)/usr/share/kde4/apps/solid/actions
	cp share/kde4/* $(DESTDIR)/usr/share/kde4/apps/solid/actions
	mkdir -p $(DESTDIR)/usr/share/icons
	cp -r share/icons/* $(DESTDIR)/usr/share/icons
	mkdir -p $(DESTDIR)/usr/share/man/man1
	install -m0644 mintstick.1 $(DESTDIR)/usr/share/man/man1
	mkdir -p $(DESTDIR)/usr/share/locale/ru/LC_MESSAGES
	msgfmt -o $(DESTDIR)/usr/share/locale/ru/LC_MESSAGES/mintstick.mo po/ru.po
