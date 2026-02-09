
import usaddress
import logging

# logging
logger = logging.getLogger(__name__)

def parse_address(address: str) -> dict:
    """
    Parse a full address string into components.
    
    Args:
        address: A full address string (e.g., "123 Internet St, City, ST 12345")
        
    Returns:
        dict: Contains keys like 'street_address', 'city', 'state', 'zip' as available.
    """
    try:
        parsed, address_type = usaddress.tag(address)
        result = {}
        
        # Map usaddress fields to street address components
        street_parts = []
        street_keys = [
            'AddressNumber', 'StreetNamePreDirectional', 'StreetNamePreModifier',
            'StreetNamePreType', 'StreetName', 'StreetNamePostType', 
            'StreetNamePostDirectional', 'SubaddressType', 'SubaddressIdentifier',
            'OccupancyType', 'OccupancyIdentifier'
        ]
        for key in street_keys:
            if key in parsed:
                street_parts.append(parsed[key])
        
        if street_parts:
            result['street_address'] = ' '.join(street_parts)
        if 'PlaceName' in parsed:
            result['city'] = parsed['PlaceName']
        if 'StateName' in parsed:
            result['state'] = parsed['StateName']
        if 'ZipCode' in parsed:
            result['zip'] = parsed['ZipCode']
            
        return result
        
    except Exception as e:
        logger.error(f"Failed to parse address '{address}': {e}")
        return {}