# settings.py

# General settings for all diagrams
node_attr = {
    "fontsize": "12",
    "fontname": "Arial Bold"
}

# You can add other general settings here in the future

import os
import sys
import subprocess

def run_all_diagrams():
    """
    Run all diagram generation scripts in their respective directories.
    This function will execute all 6 Python scripts to generate the diagrams.
    """
    # Get the directory where this settings.py file is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # List of diagram directories and their main.py files
    diagrams = [
        "aws_overall_architecture",
        "aws_network_and_data", 
        "cicd_pipeline",
        "single_vm_alternative",
        "cloudfront_fronting_alb",
        "eks_alb_ingress_with_secrets"
    ]
    
    print("🚀 Starting to generate all architecture diagrams...")
    print("=" * 50)
    
    for diagram in diagrams:
        diagram_path = os.path.join(base_dir, diagram, "main.py")
        print(f"📊 Generating {diagram} diagram...")
        
        try:
            # Run the Python script
            result = subprocess.run([
                sys.executable, diagram_path
            ], capture_output=True, text=True, cwd=os.path.join(base_dir, diagram))
            
            if result.returncode == 0:
                print(f"✅ {diagram} diagram generated successfully!")
            else:
                print(f"❌ Error generating {diagram} diagram:")
                print(f"   Error: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Failed to run {diagram}: {str(e)}")
    
    print("=" * 50)
    print("🎉 All diagrams generation completed!")
    print(f"📁 Check the PNG files in each diagram directory in: {base_dir}")

if __name__ == "__main__":
    # Allow running this script directly to generate all diagrams
    run_all_diagrams()
