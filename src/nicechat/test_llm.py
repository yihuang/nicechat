"""Command line interface for testing LLM functionality directly."""

import asyncio
from .llm import LLMClient

async def test_llm(api_key: str = None, model: str = "deepseek-chat"):
    """Test the LLM client with interactive input."""
    llm = LLMClient(api_key=api_key, model=model)
    
    def print_chunk(chunk):
        print(chunk, end='', flush=True)
    
    print("LLM Test Console (Ctrl+C to exit)")
    print(f"Using model: {model}")
    if not llm.client:
        print("⚠️ Warning: No API key provided - set DEEPSEEK_API_KEY env var or use --api-key")
    print("Type your message and press Enter:")
    
    while True:
        try:
            try:
                message = input("> ").strip()
            except EOFError:  # Handle Ctrl+D
                print("\nGoodbye!")
                break
                
            if not message:
                continue
            if message.lower() in ('/quit', '/exit', '/q'):
                print("Goodbye!")
                break
                
            print("AI: ", end='')
            try:
                response = await llm.send_message(message, callback=print_chunk)
                if not response:
                    print("\n⚠️ No response received from LLM")
                elif isinstance(response, str) and response.startswith('⚠️'):
                    print(f"\n{response}")
                else:
                    print("\n")
            except Exception as e:
                print(f"\n⚠️ Exception during LLM call: {str(e)}")
                print(f"Type: {type(e).__name__}")
            
        except KeyboardInterrupt:
            print("\nType /quit to exit or press Ctrl+C again to force quit")
            try:
                input("> ")  # Give user a chance to type /quit
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
        except Exception as e:
            print(f"\nError: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Test LLM functionality')
    parser.add_argument('--api-key', help='DeepSeek API key (defaults to DEEPSEEK_API_KEY env var)')
    parser.add_argument('--model', default='deepseek-chat',
                       help='Model to use (default: deepseek-chat)')
    args = parser.parse_args()
    
    asyncio.run(test_llm(api_key=args.api_key, model=args.model))

if __name__ == "__main__":
    main()
