# Makefile for test timer

CC          = gcc
CXX         = g++
CFLAGS      = -c -Wall -O -Wno-unused
CXXFLAGS    = -c
LDFLAGS     = -lrt -lpthread -L.
LD          = gcc
CXXLD       = g++

OBJS        = Thread.o Timer.o main.o

TARGET_APP  = main

all: $(TARGET_APP)
    @echo done.

$(TARGET_APP): $(OBJS)
    @echo "---- Build : $@ ----"
    $(LD) $(OBJS) $(LDFLAGS) -o $@

%.o: ./Timer/%.c
    $(CC) $(CFLAGS) -o $@ $<

.PHONY: clean cleanobj
clean:
    rm -f *.o
    rm -f $(TARGET_APP)

cleanobj:
    rm -f *.o