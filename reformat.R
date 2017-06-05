#!/usr/bin/env Rscript

library(dplyr)
library(readr)
library(lubridate)

args = commandArgs(trailingOnly=TRUE)

if (length(args)!=2) {
  stop("Two arguments must be provided: an input and an output dataset", call.=FALSE)
}

raw <- read.csv(
  args[1], 
  stringsAsFactors = FALSE
)

colnames(raw) = make.names(colnames(raw))

mapping <- c(
  "UserID" = "respondent_ID",
  "UserNo" = "user_no_drop",
  "Tracking.Link" = "collector_id",
  "Started" = "start_date",
  "Ended" = "end_date",
  "IP.Address" = "ip_address",
  "Email" = "email_address",
  "Name" = "first_name",
  "Unique.ID" = "unique_id_drop",
  #last_name
  "Page.Path" = "full_url",
  "Q1..Are.you.using.GOV.UK.for.professional.or.personal.reasons."="cat_work_or_personal",
  "Q2..What.kind.of.work.do.you.do."="comment_what_work",
  "Q3..Describe.why.you.came.to.GOV.UK.todayPlease.do.not.include.personal.or.financial.information..eg.your.National.Insurance.number.or.credit.card.details."="comment_why_you_came",
  "Q4..Have.you.found.what.you.were.looking.for." ="cat_found_looking_for",
  "Q5..Overall..how.did.you.feel.about.your.visit.to.GOV.UK.today." = "cat_satisfaction",
  "Q6..Have.you.been.anywhere.else.for.help.with.this.already."="cat_anywhere_else_help",
  "Q7..Where.did.you.go.for.help."="comment_where_for_help",
  "Q8..If.you.wish.to.comment.further..please.do.so.here.Please.do.not.include.personal.or.financial.information..eg.your.National.Insurance.number.or.credit.card.details."="comment_further_comments"#,
  #"Unnamed= 13"="comment_other_found_what",
  #"Unnamed= 17"="comment_other_else_help",
  #"dummy"="comment_other_where_for_help"
)

# Quick check of the column name conversions

# View(cbind(
# colnames(a),
# mapping[colnames(a)]
# ))

# Convert to data_frame

colnames(raw) <- mapping[colnames(raw)]
raw_clean_names <- as_data_frame(raw)

# Fix some disparities with the data:


fix_NA <- function(x) {
 
  x[x == ""|x=="-"] <- NA
  
  return(x)
   
}

fix_cat <- function(x) {
 
  x[!x %in% c("No","Yes","Not sure / Not yet")] <- NA
  
  return(x)
   
}

fill_other <- function(x) {

  x[x %in% c("No","Yes","Not sure / Not yet","-")] <- NA
  
  
  return(x)
  
}

fix_missing_urls <- function(x) {

  # Temporary fix to deal with missing data in the April survey
  x[x==""] <- NA
  return(x)
}

clean <- raw_clean_names %>% 
  transmute(
  # Add NA columns
  respondent_ID,
  collector_id,
  start_date = dmy_hms(start_date),
  end_date = dmy_hms(end_date),
  ip_address,
  email_address,
  first_name,
  last_name = NA, 
  full_url = fix_missing_urls(full_url),
  cat_work_or_personal = fix_NA(cat_work_or_personal),
  comment_what_work = fix_NA(comment_what_work),
  comment_why_you_came = fix_NA(comment_why_you_came),
  comment_other_found_what = fill_other(cat_found_looking_for),
  # must get comments before cleaning cat of NAs
  cat_found_looking_for = fix_cat(cat_found_looking_for),
  cat_satisfaction = fix_NA(cat_satisfaction),
  comment_other_where_for_help = fill_other(cat_anywhere_else_help),
  cat_anywhere_else_help = fix_cat(cat_anywhere_else_help),
  comment_other_else_help = NA,
  comment_where_for_help = fix_NA(comment_where_for_help),
  comment_further_comments = fix_NA(comment_further_comments)
)
# cat_anywhere_else_help

# Organise columns:

clean_organised <- clean %>%
  select(
  respondent_ID, collector_id, start_date, end_date,
  full_url, cat_work_or_personal, comment_what_work, 
  comment_why_you_came, cat_found_looking_for, comment_other_found_what, 
  cat_satisfaction, comment_other_where_for_help, cat_anywhere_else_help, 
  comment_other_else_help, comment_where_for_help, comment_further_comments 
  )


clean_organised %>% 
  write_csv(
    args[2], 
    na = ''
    )

# Exmpty fields!
# comment_other_else_help
# comment_ther_found_what


