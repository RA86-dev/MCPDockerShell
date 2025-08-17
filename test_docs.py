#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path
from main import MCPDockerServer

async def test_python_docs():
    """Test Python documentation functionality"""
    
    # Create server instance
    server = MCPDockerServer()
    
    print("🐍 Testing Python Documentation Tools")
    print("=" * 50)
    
    # Test 1: Get documentation info
    print("\n📊 Documentation Info:")
    try:
        # Manually test the functionality
        version_file = server.docs_dir / "version.txt"
        
        if not server.docs_dir.exists():
            print("❌ Python documentation not downloaded yet")
            return
        
        version = "Unknown"
        if version_file.exists():
            try:
                version = version_file.read_text().strip()
            except:
                pass
        
        # Count files
        import os
        doc_count = 0
        total_size = 0
        for root, _, files in os.walk(server.docs_dir):
            for file in files:
                if file.endswith('.txt'):
                    doc_count += 1
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except:
                        pass
        
        size_mb = total_size / (1024 * 1024)
        
        print(f"📖 Version: Python {version}")
        print(f"📁 Location: {server.docs_dir}")
        print(f"📄 Files: {doc_count} documentation files")
        print(f"💾 Size: {size_mb:.1f} MB")
        print(f"🔍 Status: Ready for AI reading and searching")
        
    except Exception as e:
        print(f"❌ Error getting documentation info: {e}")
    
    # Test 2: List some documentation files
    print("\n📋 Available Documentation Files (sample):")
    try:
        docs_files = []
        for root, _, files in os.walk(server.docs_dir):
            for file in files:
                if file.endswith('.txt'):
                    rel_path = os.path.relpath(os.path.join(root, file), server.docs_dir)
                    docs_files.append(rel_path)
        
        docs_files = sorted(docs_files)
        for i, doc in enumerate(docs_files[:10]):
            print(f"  {doc}")
        if len(docs_files) > 10:
            print(f"  ... and {len(docs_files)-10} more files")
            
    except Exception as e:
        print(f"❌ Error listing documentation: {e}")
    
    # Test 3: Search functionality
    print("\n🔍 Search Test - Looking for 'asyncio':")
    try:
        query = 'asyncio'
        query_lower = query.lower()
        results = []
        
        for root, _, files in os.walk(server.docs_dir):
            for file in files:
                if not file.endswith('.txt'):
                    continue
                    
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, server.docs_dir)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Search for query in content (case insensitive)
                    if query_lower in content.lower():
                        # Find context around matches
                        lines = content.split('\n')
                        matches = []
                        
                        for i, line in enumerate(lines):
                            if query_lower in line.lower():
                                # Get context lines
                                start = max(0, i - 1)
                                end = min(len(lines), i + 2)
                                context = '\n'.join(lines[start:end])
                                matches.append(f"Line {i+1}: {context}")
                                
                                if len(matches) >= 2:  # Limit matches per file
                                    break
                        
                        if matches:
                            results.append({
                                'file': rel_path,
                                'matches': matches[:2]  # Limit to 2 matches per file
                            })
                            
                            if len(results) >= 5:  # Limit total results
                                break
                except:
                    continue
        
        if results:
            print(f"✅ Found {len(results)} files containing '{query}':")
            for result in results:
                print(f"\n📄 {result['file']}:")
                for match in result['matches']:
                    # Truncate very long lines
                    lines = match.split('\n')
                    for line in lines:
                        if len(line) > 100:
                            line = line[:97] + "..."
                        print(f"   {line}")
        else:
            print(f"❌ No matches found for '{query}'")
            
    except Exception as e:
        print(f"❌ Error searching documentation: {e}")
    
    # Test 4: Read a specific file
    print("\n📖 Sample Documentation Content:")
    try:
        # Try to read the contents.txt file
        contents_file = server.docs_dir / 'contents.txt'
        if contents_file.exists():
            with open(contents_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Show first 15 lines
            print(f"First 15 lines of contents.txt:")
            for i, line in enumerate(lines[:15]):
                print(f"   {line.rstrip()}")
            
            if len(lines) > 15:
                print(f"   ... and {len(lines)-15} more lines")
        else:
            print("❌ contents.txt not found")
            
    except Exception as e:
        print(f"❌ Error reading documentation file: {e}")
    
    print("\n✅ Python documentation testing complete!")

if __name__ == "__main__":
    asyncio.run(test_python_docs())