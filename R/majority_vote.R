majority_vote <- function(x) {
  
  # This function is used for calculating a majority vote among
  # manual classifications from the GOV.UK user intent survey.
  
  x = as.character(x)
  x = na.omit(x)
  
  if (!length(x)) {
    
    out <- NA
    
  } else {
    
    # Need clause here for dealing with all NAs
    
    xu <- unique(x)
    
    y = vector(
      mode = 'integer', 
      length = length(xu)
    )
    
    for (i in 1:length(xu)) {
      y[i] <- sum(x == xu[i])
    }
    
    y <- which(y == max(y))
    if (length(y) > 1) {
      
      out = NA
      
    } else {
      out <- xu[y]
    }
    
  }
  
  return(out)
  
}
