import datetime as dt
import time
import random
import logging

default_limit = 100

from optibook.synchronous_client import Exchange
from libs import print_positions_and_pnl, round_down_to_tick, round_up_to_tick

from IPython.display import clear_output


def insert_quotes(exchange, instrument, bid_price, ask_price, bid_volume, ask_volume):
    if bid_volume > 0:
        # Insert new bid limit order on the market
        exchange.insert_order(
            instrument_id=instrument.instrument_id,
            price=bid_price,
            volume=bid_volume,
            side='bid',
            order_type='limit',
        )
        
        # Wait for some time to avoid breaching the exchange frequency limit
        time.sleep(0.05)

    if ask_volume > 0:
        # Insert new ask limit order on the market
        exchange.insert_order(
            instrument_id=instrument.instrument_id,
            price=ask_price,
            volume=ask_volume,
            side='ask',
            order_type='limit',
        )

        # Wait for some time to avoid breaching the exchange frequency limit
        time.sleep(0.05)
    
exchange = Exchange()
exchange.connect()

INSTRUMENTS = exchange.get_instruments()

QUOTED_VOLUME = 10
FIXED_MINIMUM_CREDIT = 0.15
PRICE_RETREAT_PER_LOT = 0.005
POSITION_LIMIT = 100

while True:
    print(f'')
    print(f'-----------------------------------------------------------------')
    print(f'TRADE LOOP ITERATION ENTERED AT {str(dt.datetime.now()):18s} UTC.')
    print(f'-----------------------------------------------------------------')

    # Display our own current positions in all stocks, and our PnL so far
    print_positions_and_pnl(exchange)
    print(f'')
    print(f'          (ourbid) mktbid :: mktask (ourask)')
    
    #callAI('this is a test')
    social_feeds = exchange.poll_new_social_media_feeds()
    
    if not social_feeds:
        print(f'{dt.datetime.now()}: no new messages')
    else:
        for feed in social_feeds:
            print(f'{feed.timestamp}: {feed.post}')
            
    
    
    for instrument in INSTRUMENTS.values():
        # Remove all existing (still) outstanding limit orders
        exchange.delete_orders(instrument.instrument_id)
        if "_B" not in instrument.instrument_id:
            positions_2 = exchange.get_positions()[instrument.instrument_id + '_B']
            instrument_order_book_DL = exchange.get_last_price_book(instrument.instrument_id + '_B')
            if not (instrument_order_book_DL and instrument_order_book_DL.bids and instrument_order_book_DL.asks):
                print(f'{instrument.instrument_id + :>6s} --     INCOMPLETE ORDER BOOK DUAL LISTING')
                continue
            best_bid_price_DL = instrument_order_book_DL.bids[0].price
            best_ask_price_DL = instrument_order_book_DL.asks[0].price
            
           
           
        # Obtain order book and only skip this instrument if there are no bids or offers available at all on that instrument,
        # as we we want to use the mid price to determine our own quoted price
        instrument_order_book = exchange.get_last_price_book(instrument.instrument_id)
       
        if not (instrument_order_book and instrument_order_book.bids and instrument_order_book.asks):
            print(f'{instrument.instrument_id:>6s} --     INCOMPLETE ORDER BOOK')
            continue
    
        # Obtain own current position in instrument
        position = exchange.get_positions()[instrument.instrument_id]
        
      

        # Obtain best bid and ask prices from order book to determine mid price
        best_bid_price = instrument_order_book.bids[0].price
        best_ask_price = instrument_order_book.asks[0].price
        mid_price = (best_bid_price + best_ask_price) / 2.0 
        
        # Obtain best bid and ask prices from order book to determine mid price
        best_bid_volume = instrument_order_book.bids[0].volume
        best_ask_volume = instrument_order_book.asks[0].volume
        best_bid_volume_DL = instrument_order_book_DL.bids[0].volume
        best_ask_volume_DL = instrument_order_book_DL.asks[0].volume
        
        # Calculate bid and ask volumes to insert, taking into account the exchange position_limit
        max_volume_to_buy = POSITION_LIMIT - position
        max_volume_to_sell = POSITION_LIMIT + position  
        
        current_bid_volume = best_bid_volume
        current_ask_volume = best_ask_volume
        current_bid_volume_DL = best_bid_volume_DL
        current_ask_volume_DL = best_ask_volume_DL
        actual_volume_to_buy = 0
        
        # Index for Dual Listing comparison
        dual_listing_index_bid = 0
        dual_listing_index_ask = 0
        
        while( current_ask_price_DL < best_bid_price and max_volume_to_buy > 0):
            if(max_volume_to_buy > best_bid_volume):
                actual_volume_to_buy += best_bid_volume
                dual_listing_index_bid += 1
            if( current_ask_volume_DL < current_bid_volume)
                actual_volume_to_buy += current_ask_volume
                dual_listing_index_ask += 1
            break
                
            
        while( best_bid_price_DL > best_ask_price):
            pass
        
        # Calculate our fair/theoretical price based on the market mid price and our current position
        theoretical_price = mid_price - PRICE_RETREAT_PER_LOT * position

        # Calculate final bid and ask prices to insert
        bid_price = round_down_to_tick(theoretical_price - FIXED_MINIMUM_CREDIT, instrument.tick_size)
        ask_price = round_up_to_tick(theoretical_price + FIXED_MINIMUM_CREDIT, instrument.tick_size)
        
        

        bid_volume = min(QUOTED_VOLUME, max_volume_to_buy)
        ask_volume = min(QUOTED_VOLUME, max_volume_to_sell)

        # Display information for tracking the algorithm's actions
        print(f'{instrument.instrument_id:>6s} -- ({bid_price:>6.2f}) {best_bid_price:>6.2f} :: {best_ask_price:>6.2f} ({ask_price:>6.2f})')
        
        # Insert new quotes
        insert_quotes(exchange, instrument, bid_price, ask_price, bid_volume, ask_volume)
        
    # Wait for a few seconds to refresh the quotes
    print(f'\nWaiting for 2 seconds.')
    #time.sleep(2)
    
    # Clear the displayed information after waiting
    clear_output(wait=True)