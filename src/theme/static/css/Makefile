sources := style.less \
           about.less \
           colors.less \
           comments.less \
           content.less \
           footer.less \
           header.less \
           images.less \
           pygments.css \
           table-of-contents.less \
           tables.less

intermediate := pygments.css

output := style.css

all: $(output)
.PHONY: all

clean:
	-rm -rf $(output) $(intermediate)
.PHONY: clean

pygments.css:
	pygmentize -f html -S colorful -a .highlight > $@

$(output): $(sources) $(intermediate)
	lessc $< > $@-new
	mv -f $@-new $@
