# Data Generator
Random and weighted data generator for Pandas' data frames.

## Methods

  ### random_ints / random_floats (n, a, b)
  Generates array with n random integer/floating numbers from 'a (lower bound) to b (higher bound).

  ### random_values (n, values)
  Generates array with n random values from values list.

  ### random_values_with_probs (n, values, p)
  Generates array with n random values from values list, biased on p list of probabilities. 

  ### random_names (n)
  Generates array with n random names from faker library.

## To-do's
### random_addresses (n)
Will generate array with n random addresses from faker library.

### generate_dataset (n, fields, values, p)
Will generate dataset with columns based on fields list. Values will be retrieved from values dictionary and biased by p.
