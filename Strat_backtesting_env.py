import bisect
import matplotlib.pyplot as plt
import numpy as np


class LiquidityPool:
    def __init__(self, inital_price, fee_tier, silence_mode=True, gov=0.1):
        self.positions = {}
        self.ticks = {}  # Stores liquidity at each tick
        self.ordered_ticks = []
        self.current_price = inital_price  # Initial price, can be set to market open or an arbitrary value
        self.l = 0
        self.upper = np.inf
        self.lower = 0
        self.fee_tier = fee_tier/100
        self.fg_0 = 0
        self.fg_1 = 0
        self.gov = gov # governance fee %
        self.inform = not silence_mode


    def add_position_liquidity(self, lower_tick, upper_tick, liquidity):
        
        if self.current_price == None:
            raise RuntimeError("You are the first one to set a position, please use the 'add_first_custom_position' instead")


        # Update liquidity at each tick
        for tick in [lower_tick, upper_tick]:
            sign = lambda x : 1 if x == lower_tick else -1
            if tick in self.ticks:
                self.ticks[tick]['delta_l'] += sign(tick)*liquidity
            else:
                fg1, fg0 = self.fg_1 if self.current_price >= tick else 0, self.fg_0 if self.current_price >= tick else 0
                self.ticks[tick] = {'delta_l': sign(tick)*liquidity, 'fo_0': fg0, 'fo_1': fg1}

        if self.current_price <= upper_tick and self.current_price >= lower_tick:
            self.l += liquidity
            if upper_tick < self.upper:
                self.upper = upper_tick
            if lower_tick > self.lower:
                self.lower = lower_tick

        bisect.insort(self.ordered_ticks, lower_tick)
        bisect.insort(self.ordered_ticks, upper_tick)

        if (lower_tick,upper_tick) in self.positions:
            f0 = self.get_position_fees(lower_tick, upper_tick, 0)
            f1 = self.get_position_fees(lower_tick, upper_tick, 1)
            self.positions[(lower_tick,upper_tick)]['liquidity'] += liquidity
        else:
            self.positions[(lower_tick,upper_tick)] = {
                'lower_tick': lower_tick,
                'upper_tick': upper_tick,
                'liquidity': liquidity,
                'fg_last_0': 0,
                'fg_last_1': 0
            }

            for token in [0,1]:
                fo_u, fo_l = self.ticks[upper_tick][f'fo_{token}'], self.ticks[lower_tick][f'fo_{token}']
                fg = self.fg_0 if token == 0 else self.fg_1
                fb = fo_l if self.current_price >= lower_tick else fg-fo_l
                fa = fg-fo_u if self.current_price >= upper_tick else fo_u
                fr = fg - fb - fa
                self.positions[(lower_tick,upper_tick)][f'fg_last_{token}'] = fr

            f0, f1 = 0,0

        return f0, f1
        
    def add_custom_position(self, lower_tick, upper_tick, amount, token):
        """
        token : 0 or 1 depending on which currency you are providing
        This function adds liquidity valued at the amount given (in token0 or in token1) : 
        The amount of token given is not the amount minted in the case where the current price inside the added position,
        it rather represents tha value of the added position in Toke0 or in Token1.
        """

        if token not in [0,1]:
            raise ValueError("Token value error, please choose 0 or 1 depending on which currency you're providing")
        if self.current_price == None:
            raise RuntimeError("You are the first one to set a position, please use the 'add_first_custom_position' instead")
        if self.current_price < lower_tick:
            if token == 1:
                raise ValueError("The price is bellow the range provided, you can only create a position using token0")
            else:
                liquidity = amount / ((1/np.sqrt(lower_tick))-(1/np.sqrt(upper_tick)))
        elif self.current_price > upper_tick:
            if token == 1:
                liquidity = amount / (np.sqrt(upper_tick)-np.sqrt(lower_tick))
            else:
                raise ValueError("The price is above the range provided, you can only create a position using token1")
        else:
            if token == 0:
                liquidity = amount * self.current_price / ((np.sqrt(upper_tick) - np.sqrt(self.current_price)) / (np.sqrt(self.current_price) * np.sqrt(upper_tick)) * self.current_price + (np.sqrt(self.current_price) - np.sqrt(lower_tick)))
            else:
                liquidity = amount / (((np.sqrt(upper_tick) - np.sqrt(self.current_price)) / (np.sqrt(self.current_price) * np.sqrt(upper_tick))) * self.current_price + (np.sqrt(self.current_price) - np.sqrt(lower_tick)))

        self.add_position_liquidity(lower_tick, upper_tick, liquidity)


    def add_allocation(self, wealth: float, weights: list, bins: list):
        """
        wealth: Total amount of token1 to allocate
        bins: Buckets indexed by their left limit
        weights: weights[i] gives the proportion of the wealth to be added to the bucket bins[i] 
        """
        for i in range(len(bins)-1):
            if bins[i] > self.current_price:
                if self.inform :
                    print(f"Automatic exchange of tokens to mint liquidity in position {(bins[i], bins[i+1])}")
                self.add_custom_position(bins[i], bins[i+1], (wealth*weights[i])/self.current_price, 0)
            else:
                self.add_custom_position(bins[i], bins[i+1], wealth*weights[i], 1)

        if self.inform :
            print('Allocation made successfully !')
            

    def remove_position(self, lower_tick, upper_tick):
        # Removing a liquidity position
        if (lower_tick, upper_tick) in self.positions:
            position = self.positions.pop((lower_tick, upper_tick))
            for tick in [position['lower_tick'], position['upper_tick']]:
                sign = lambda x : 1 if x == position['lower_tick'] else -1
                self.ticks[tick]['delta_l'] -= sign(tick)*position['liquidity']
                if self.inform :
                    print('Burned liquidity in Tokens amounts (token0,token1)')

            if self.current_price <= upper_tick and self.current_price >= lower_tick:
                self.l -= position['liquidity']
            return self.liquidity_equivalent(position['liquidity'], lower_tick, upper_tick)
        
        else:
            raise KeyError("The position tick limits provided do not match any of the existing positions")
    

    def burn_liquidity(self, lower_tick, upper_tick, l):
        # Removing a liquidity position
        
        if (lower_tick, upper_tick) in self.positions:
            f0 = self.get_position_fees(lower_tick, upper_tick, 0)
            f1 = self.get_position_fees(lower_tick, upper_tick, 1)
            position = self.positions[(lower_tick, upper_tick)]
            if l < self.positions[(lower_tick, upper_tick)]['liquidity']:
                position['liquidity'] -= l
                self.ticks[position['lower_tick']]['delta_l'] -= l 
                self.ticks[position['upper_tick']]['delta_l'] += l

                if self.current_price <= upper_tick and self.current_price >= lower_tick:
                    self.l -= l
                if self.inform :
                    print('Burned liquidity in Tokens amounts (token0,token1)')
                return self.liquidity_equivalent(l, lower_tick, upper_tick), f0, f1
            
            else:
                if self.inform :
                    print("Position removed since burned liquidity exceed the position's available liquidity")
                    print('Burned liquidity in Tokens amounts (token0,token1)')
                self.remove_position(lower_tick, upper_tick)
                return self.liquidity_equivalent(position['liquidity'], lower_tick, upper_tick), f0, f1
                
        else:
            raise KeyError("The position tick limits provided do not match any of the existing positions")

    
    def swap_price(self, price):
        test = price > self.current_price
        next_price = price
        while next_price > self.upper:

            # The actual impact of DeltaX on the pool is the remaining after paying the fees !
            self.fg_1 += (1-self.gov) * self.fee_tier * ((np.sqrt(self.upper)-np.sqrt(self.current_price)) / (1-self.fee_tier)) 
            pos = bisect.bisect_right(self.ordered_ticks, self.upper)
            
            if pos >= 0 and pos <len(self.ordered_ticks):
                self.l += self.ticks[self.upper]['delta_l']
                self.ticks[self.upper]['fo_0'] = self.fg_0 - self.ticks[self.upper]['fo_0'] 
                self.ticks[self.upper]['fo_1'] = self.fg_1 - self.ticks[self.upper]['fo_1'] 
                self.lower = self.upper
                self.current_price = self.upper
                self.upper = self.ordered_ticks[pos]
            else:
                self.l += self.ticks[self.upper]['delta_l']
                self.ticks[self.upper]['fo_0'] = self.fg_0 - self.ticks[self.upper]['fo_0'] 
                self.ticks[self.upper]['fo_1'] = self.fg_1 - self.ticks[self.upper]['fo_1'] 
                self.lower= self.upper
                self.upper = float('inf')
                
                if self.inform :
                    print("The price is out of the LP's positions !")
                break

        while next_price < self.lower:

            self.fg_0 += (1-self.gov) * self.fee_tier * ((1/np.sqrt(self.lower)-1/np.sqrt(self.current_price))/ (1-self.fee_tier))
            pos = bisect.bisect_left(self.ordered_ticks, self.lower)

            if pos > 0:
                self.l -= self.ticks[self.lower]['delta_l']
                self.ticks[self.lower]['fo_0'] = self.fg_0 - self.ticks[self.lower]['fo_0'] 
                self.ticks[self.lower]['fo_1'] = self.fg_1 - self.ticks[self.lower]['fo_1'] 
                self.upper = self.lower
                self.current_price = self.lower
                self.lower = self.ordered_ticks[pos - 1]
            else:
                self.l -= self.ticks[self.lower]['delta_l']
                self.ticks[self.lower]['fo_0'] = self.fg_0 - self.ticks[self.lower]['fo_0'] 
                self.ticks[self.lower]['fo_1'] = self.fg_1 - self.ticks[self.lower]['fo_1'] 
                self.upper = self.lower
                self.lower = -float('inf')
                if self.inform :
                    print("The price is out of the LP's positions !")
                break
        if test :
            self.fg_1 += (1-self.gov) *self.fee_tier * ((np.sqrt(price)-np.sqrt(self.current_price))/ (1-self.fee_tier))
        else:
            self.fg_0 += (1-self.gov) * self.fee_tier * ((1/np.sqrt(price)-1/np.sqrt(self.current_price))/ (1-self.fee_tier))

        self.current_price = price
        return True


    def plot_liquidity(self, focus = False):

        srtd = dict(sorted(self.ticks.items()))
        
        x_values = list(srtd.keys())
        y_values = np.array([d['delta_l'] for d in srtd.values()]).cumsum()
    
        # Calculate the differences between consecutive x_values
        widths = np.diff(x_values, append=x_values[-1]+1)
        
        plt.figure(figsize=(20,10))
        plt.bar(x_values, y_values, align='edge', width=widths)

        if focus:
            plt.bar([self.positions[focus]["lower_tick"]],[self.positions[focus]["liquidity"]], align='edge', width=[self.positions[focus]["upper_tick"]-self.positions[focus]["lower_tick"]], color='cyan')

        prec = 0
        for x, y in zip(x_values, y_values):
            plt.plot([x, x], [0, max(y,prec)], color='r', linestyle='-')
            prec = y
        
        plt.xlabel('Price')
        plt.ylabel('Liquidity')
        plt.title('Available liquidity')
        plt.show()
    

    def liquidity_equivalent(self, liquidity, lower, upper):
        if upper < self.current_price:
            token0, token1 = 0, liquidity * (np.sqrt(upper)-np.sqrt(lower))
        elif self.current_price < lower:
            token0, token1 = liquidity * ((1/np.sqrt(lower))-(1/np.sqrt(upper))), 0
        else:
            token0, token1 = liquidity * ((1/np.sqrt(self.current_price))-(1/np.sqrt(upper))), liquidity * (np.sqrt(self.current_price)-np.sqrt(lower))
        return token0, token1
    

    def get_position_comp(self, lower, upper):
        position = self.positions[(lower, upper)]
        l = position['liquidity']
        
        return self.liquidity_equivalent(l, lower, upper)


    def get_position_fees(self, lower, upper, token):
        if token not in [0,1]:
            raise ValueError("Token value error, please choose 0 or 1 depending on which currency you're providing")

        l = self.positions[(lower,upper)]['liquidity']
        
        fo_u, fo_l = self.ticks[upper][f'fo_{token}'], self.ticks[lower][f'fo_{token}']

        fg = self.fg_0 if token == 0 else self.fg_1
        fb = fo_l if self.current_price >= lower else fg-fo_l
        fa = fg-fo_u if self.current_price >= upper else fo_u
        fr = fg - fb - fa
        
        fees = fr-self.positions[(lower, upper)][f'fg_last_{token}']
        self.positions[(lower, upper)][f'fg_last_{token}'] = fr

        if self.inform :
            print(f"Fees collected in token{token} : {fees*l}")

        return fees * l
       

    def get_position_value(self, lower, upper, add_fees=True):

        token0, token1 = self.get_position_comp(lower, upper)
        if add_fees:
            token0 += self.get_position_fees(lower, upper, 0)-self.positions[lower, upper][f'fg_last_0']
            token1 += self.get_position_fees(lower, upper, 1)-self.positions[lower, upper][f'fg_last_1']

        return token1 + token0 * self.current_price


    def get_allocation_value(self, add_fees=True):
        val = 0
        for pos in self.positions :
            val += self.get_position_value(pos[0], pos[1], add_fees=add_fees)

        return val

    def get_allocation_comp(self):
        token0, token1 = 0, 0
        for pos in self.positions :
            x, y = self.get_position_comp(pos[0], pos[1])
            token0 += x
            token1 += y

        return token0, token1

    def uncollected_position_fees_info(self, lower, upper , token):
        fr = self.get_position_fees(lower, upper, token)
        if self.inform :
            print(f"Uncollected fees in token{token} : {fr-self.positions[(lower, upper)][f'fg_last_{token}']}")
