def message(result):
    list_of_messages = [
    {"value": 0, "name": "MAV_RESULT_ACCEPTED", "description": "Command is valid (is supported and has valid parameters), and was executed."},
    {"value": 1, "name": "MAV_RESULT_TEMPORARILY_REJECTED", "description": "Command is valid, but cannot be executed at this time. Retry later may work."},
    {"value": 2, "name": "MAV_RESULT_DENIED", "description": "Command is invalid (supported but has invalid parameters). Retrying won't work."},
    {"value": 3, "name": "MAV_RESULT_UNSUPPORTED", "description": "Command is not supported (unknown)."},
    {"value": 4, "name": "MAV_RESULT_FAILED", "description": "Command is valid, but execution failed due to a non-temporary error."},
    {"value": 5, "name": "MAV_RESULT_IN_PROGRESS", "description": "Command is valid and being executed. Final result will follow."},
    {"value": 6, "name": "MAV_RESULT_CANCELLED", "description": "Command has been cancelled by a COMMAND_CANCEL message."},
    {"value": 7, "name": "MAV_RESULT_COMMAND_LONG_ONLY", "description": "Command is only accepted as COMMAND_LONG."},
    {"value": 8, "name": "MAV_RESULT_COMMAND_INT_ONLY", "description": "Command is only accepted as COMMAND_INT."},
    {"value": 9, "name": "MAV_RESULT_COMMAND_UNSUPPORTED_MAV_FRAME", "description": "Invalid command due to unsupported MAV_FRAME."}
    ]
    
    # Extract the value from result list (assuming format [["command_name", value]])
    if result and len(result) > 0 and len(result[0]) > 1:
        result_value = result[0][1]  # Get the value from ["take_off", 0]
        print(result_value)
        # Find matching message
        for message_item in list_of_messages:
            if message_item["value"] == result_value:
                #print(f"Command: {result[0][0]}")
                #print(f"Result: {message_item['name']}")
                print(f"Description: {message_item['description']}")
                return
        
        # If no match found
        print(f"No matching message found for value: {result_value}")
    else:
        print("Invalid result format")

result = [["take_off", 0]]
message(result)