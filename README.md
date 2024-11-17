
# Liquidity Pool Utilities

This module provides utilities for managing a liquidity pool, in accordance with the innovative approach of the Uniswap V3, allowing the addition of positions, updating of liquidity, and tracking of fees and positions. Moreover, you can find our backtesting environement in *Strat_backtesting_env*, along with its usage and other valuable analysis in *Analysis_notebooks*. A detailed explanation of the work is coming soon. For now you can find bellow the details of our Uniswap V3 simulator.

## Table of Contents

- [Functions and Methods](#functions-and-methods)
  - [LiquidityPool Class](#liquiditypool-class)
- [Usage](#usage)

- [Installation](#installation)
- [License](#license)

## Functions and Methods

### LiquidityPool Class

#### Methods:

- `__init__(self, fee_tier)`: Initializes the liquidity pool with the specified fee tier.
- `add_first_custom_position(self, lower_tick, upper_tick, amount_token0, amount_token1)`: Adds the first position to set the initial price, given an amount of each token.
- `add_position_liquidity(self, lower_tick, upper_tick, liquidity)`: Adds a new liquidity position, as long as the pool contains other positions. It requires a price range and a given amount of liquidity.
- `add_custom_position(self, lower_tick, upper_tick, amount, token)`: Adds a new liquidity position, as long as the pool contains other positions. It requires a price range and a given amount of one of the tokens.
- `remove_position(self, lower_tick, upper_tick, liquidity)`: Removes a position from the pool.
- `swap(self, token_in, amount_in, direction)`: Executes a swap operation, following Uniswap V3's theory.
- `set_price(self, price)`: Sets the current price of the liquidity pool, by executing a fictive swap resulting in the target price.
- `get_position_comp(self, id)`: Calculates the amount of each token in a given position.
- `get_position_value(self, id, token, add_fees=True)`: Calculates the value of a position in terms of a the given token, giving the option of not including the fees.
- `get_positions_fees(self, id, token)`: Calculates the fees cumulated by position cumulated in the given token from its initialization.  This method is only used internaly by the two following method.
- `uncollected_position_fees_info(self, id, token)`: Prints information about uncollected fees of a position cumulated in the given token.
- `collect_position_fees(self, id, token)`: Collects the fees from a position, cumulated in the given token.
- `plot_liquidity(self, focus = False)`: Plots the distribution of available liquidity across the initialized ticks.

## Usage

Please refer to *UNISWAP.ipynb* notebook for a live tutorial on how to correctly use our tool.

## Installation

Ensure you have the following dependencies installed:

- bisect
- matplotlib
- numpy

You can install them using pip:

```sh
pip install matplotlib numpy
```

## License

This module is provided under the Mazars License.
