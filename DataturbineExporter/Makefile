JAVAC     := javac
JAR       := jar

# A dumb hack to autogenerate the classpath from the deps list.
EMPTY     :=
SPACE     := $(EMPTY) $(EMPTY)

SRC_DIR   := edu/scu/engr/rsl/deca
BLD_DIR   := build
SOURCES   := $(wildcard $(SRC_DIR)/*.java)
CLASSES   := $(addprefix $(BLD_DIR)/,$(SOURCES:.java=.class))

MANIFEST  := manifest/manifest.txt
TARGET    := $(BLD_DIR)/DataturbineExporter.jar
DEPS      := rbnb.jar juds.jar
CLASSPATH := $(subst $(SPACE),:,$(DEPS))

.PHONY: all clean

all: $(TARGET)

$(CLASSES): | $(BLD_DIR)/$(SRC_DIR)/

# The way jar works is colossally dumb.
$(TARGET): $(CLASSES)
#	@printf "\e[1;32m%5s\e[m $@\n" JAR
	@$(JAR) cfm $@ $(MANIFEST) $(addprefix -C $(BLD_DIR) ,$(subst $(BLD_DIR)/,,$^))
	@cp $(DEPS) $(BLD_DIR)

$(BLD_DIR)/%.class: %.java
#	@printf "\e[1;34m%5s\e[m $<\n" JAVAC
	@$(JAVAC) -classpath $(CLASSPATH) -sourcepath . -d $(BLD_DIR) $<

$(BLD_DIR):
	@printf "\e[1;33m%5s\e[m $@\n" MKDIR
	@mkdir -p $@

$(BLD_DIR)/%/: | $(BLD_DIR)
	@printf "\e[1;33m%5s\e[m $@\n" MKDIR
	@mkdir -p $@

clean:
	@printf "\e[1;31m%5s\e[m $(BLD_DIR)\n" RM
	@rm -rf $(BLD_DIR)
