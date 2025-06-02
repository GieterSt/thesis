#!/bin/bash

echo "🚀 Setting up LLM Greenhouse LED Optimization Repository"
echo "======================================================"

# Initialize git repository
echo "📝 Initializing git repository..."
git init

# Add all files
echo "📁 Adding all files..."
git add .

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: LLM Performance Evaluation for Greenhouse LED Scheduling

Features:
- Comprehensive evaluation of 6 LLM models
- Google Gemini post-processing breakthrough (4.3% → 100% success)
- Complete analysis framework with ground truth integration
- Performance visualizations and detailed documentation
- Production-ready deployment recommendations

Key Results:
- Google Gemini 2.5 Pro Preview: 100% API success, 47.8% optimization accuracy (post-processed)
- OpenAI O1: 60% API success, 0% optimization accuracy  
- Claude Opus 4: 100% API success, 0% optimization accuracy
- Llama 3.3 70B: 100% API success, 0% optimization accuracy"

# Set up remote repository
echo "🔗 Setting up remote repository..."
git branch -M main
git remote add origin https://github.com/GieterSt/thesis.git

# Push to repository
echo "⬆️ Pushing to GitHub..."
git push -u origin main

echo ""
echo "✅ Repository setup complete!"
echo "🌐 View your repository at: https://github.com/GieterSt/thesis"
echo ""
echo "📊 Summary of what was uploaded:"
echo "• Complete LLM evaluation research"
echo "• Post-processing breakthrough documentation"
echo "• All analysis scripts and results"
echo "• Performance visualizations"
echo "• Production deployment recommendations" 