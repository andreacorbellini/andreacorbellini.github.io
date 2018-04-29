BOOTSTRAP_VERSION := 3.3.6

TMPDIR := $(shell mktemp -du)

all: css/style.css

clean:
	-rm -rf \
		css/style.css \
		css/style.css-new \
		css/style.min.css \
		css/pygments.css \
		bootstrap

.PHONY: all clean

bootstrap:
	mkdir $(TMPDIR)
	wget -O $(TMPDIR)/bootstrap.zip \
		https://github.com/twbs/bootstrap/archive/v$(BOOTSTRAP_VERSION).zip
	unzip -d $(TMPDIR) $(TMPDIR)/bootstrap.zip
	mkdir -p $@
	mv $(TMPDIR)/bootstrap-$(BOOTSTRAP_VERSION)/less/* $@
	-rm bootstrap/variables.less
	-rm -rf $(TMPDIR)

bootstrap/variables.less: bootstrap variables.less
	cp variables.less bootstrap

css/pygments.css:
	pygmentize -f html -S colorful -a .highlight > $@

css/style.css: css/style.less css/pygments.css bootstrap bootstrap/variables.less
	lessc $< > $@-new
	mv -f $@-new $@

css/style.min.css: css/style.css
	cleancss -o $@ $<
