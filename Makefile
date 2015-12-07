BIN=$(shell npm bin)
BUILT=build/index.js
watch:
	mkdir -p build
	$(BIN)/watchify -t coffeeify -o $(BUILT) src/main.coffee & \
	$(BIN)/browser-sync start --server --files=$(BUILT)
