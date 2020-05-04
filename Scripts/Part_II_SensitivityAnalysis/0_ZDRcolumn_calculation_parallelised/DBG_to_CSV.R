#!/path_to_R_installation
# This Script processes the DEBUG-ZDRCOLC output
# and stores it in a CSV-file
#
# Principle is:
# 1) Trim spaces
# 2) grep + extract pattern
# 3) Write CSV with new Integer/Double-Type Values
#
# Script written by Christoph von Matt

# adding library-paths
.libPaths(c("path_to_Rlibrary", .libPaths()))

# Passing WD will not be necessary if directly piped in input
library(readr)

print("Starting Preprocessing for Filtering-File")
###### PART ONE ######
# Specifications of colnames and number of columns
var_names <- c("radar", "y", "x", "hgt", "hzero", "ZDR", "ZH")
var_n <- length(var_names)


# Read-In File (will be cancelled by direct input)
f <- file("stdin")
open(f)

# Output-Filename specification
args <- commandArgs(trailingOnly=T)
outpath <- args[1]
time <- args[2]
outname <- paste(time, ".csv", sep="")

# Reading-in all lines
file <- readLines(f)

file <- as.matrix(file)
nr_lines <- length(file)

print("Lines read")

# change directory to outpath
setwd(outpath)

# subset data for testing
#file <- file[1:1000]

# Split data for unequal line lengths due to decimal numbers
lines_short <- file[which(nchar(file) == 61)]
nr_short <- length(lines_short)
lines_long <- file[which(nchar(file) == 63)]
nr_long <- length(lines_long)
rm(file)

###############
# SHORT_LINES
lines_short <- as.matrix(lines_short, nrow=nr_short, ncol=1)

part1 <- matrix(NA, nrow=nr_short, ncol=var_n)
#system.time({
  part1[,1] <- as.numeric(apply(lines_short, 2, substr, 10, 10))
  part1[,2] <- as.numeric(apply(lines_short, 2, substr, 14, 17))
  part1[,3] <- as.numeric(apply(lines_short, 2, substr, 20, 23))
  part1[,4] <- as.numeric(apply(lines_short, 2, substr, 29, 31))
  part1[,5] <- as.numeric(apply(lines_short, 2, substr, 39, 43))
  part1[,6] <- as.numeric(apply(lines_short, 2, substr, 48, 51))
  part1[,7] <- as.numeric(apply(lines_short, 2, substr, 56, 61))
#})

###############
# LONG_LINES (with more characters due to decimal numbers in processed string
lines_long <- as.matrix(lines_long, nrow=nr_long, ncol=1)

part2 <- matrix(NA, nrow=nr_long, ncol=var_n)
#system.time({
  part2[,1] <- as.numeric(apply(lines_long, 2, substr, 10, 10))
  part2[,2] <- as.numeric(apply(lines_long, 2, substr, 14, 17))
  part2[,3] <- as.numeric(apply(lines_long, 2, substr, 20, 23))
  part2[,4] <- as.numeric(apply(lines_long, 2, substr, 29, 31))
  part2[,5] <- as.numeric(apply(lines_long, 2, substr, 39, 43))
  part2[,6] <- as.numeric(apply(lines_long, 2, substr, 48, 53))
  part2[,7] <- as.numeric(apply(lines_long, 2, substr, 58, 63))
#})

final <- rbind(part1, part2)
colnames(final) <- var_names

###############

print("Conversion done!")

final <- as.data.frame(final)
write_csv(final, outname, col_names=T)

print("File written")
