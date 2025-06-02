# Prompt Engineering Evolution

This directory documents the evolution of prompts used in the LLM LED optimization evaluation study.

## Overview

The research tested three distinct prompt engineering approaches to optimize LLM performance on constrained optimization tasks. Each version built upon lessons learned from the previous iteration.

## Prompt Versions

### V1: Basic Task Description
**File**: `../data/test_sets/test_set_v1.json`

**Approach**: Minimal prompt with basic task description
**Key Elements**:
- Simple problem statement
- Basic parameter specification
- JSON output format request

**Example**:
```
You are tasked with optimizing LED lighting schedules for a greenhouse to achieve specific daily PPFD targets while minimizing electricity costs.

Key Parameters:
- LED Power Output: 275 μmol/m²/s per LED unit
- Electricity prices vary by hour throughout the day
- Daily PPFD target must be achieved
- LED units can be adjusted hourly (0-23 hours)
- Goal: Minimize electricity cost while meeting PPFD target

Please provide your LED allocation for each hour in JSON format:
{
  "led_allocations": [hour0, hour1, hour2, ..., hour23]
}
```

**Results**: Baseline performance, some JSON compliance issues

### V2: Enhanced Instructions with Role Definition
**File**: `../data/test_sets/test_set_v2.json`

**Approach**: Comprehensive prompt with role definition, algorithm guidance, and examples
**Key Enhancements**:
- Expert role definition ("LED scheduling optimizer")
- Step-by-step optimization algorithm
- Detailed constraint specification
- Concrete example allocation
- Final validation instruction

**Example**:
```
You are an expert LED scheduling optimizer for greenhouse operations. Your role is to create cost-effective lighting schedules that meet daily PPFD targets while minimizing electricity expenses.

SYSTEM OVERVIEW:
- LED Power Output: 275 μmol/m²/s per LED unit
- Operating Window: 24 hours (0-23)
- Objective: Minimize electricity cost while achieving daily PPFD target

OPTIMIZATION ALGORITHM:
1. Calculate total daily PPFD requirement
2. Identify hours with lowest electricity prices
3. Prioritize LED allocation during cost-effective periods
4. Ensure daily PPFD target is exactly met
5. Minimize total electricity expenditure

CONSTRAINTS:
- Daily PPFD target must be achieved (±0.1% tolerance)
- LED units must be non-negative integers
- Each LED contributes 275 μmol/m²/s when active
- Hourly allocations can vary from 0 to maximum available

EXAMPLE ALLOCATION:
For 20 mol/m²/day target with varying electricity prices:
- Prioritize hours 2-6 (lowest prices: 0.05-0.08 €/kWh)
- Use hours 10-14 if additional PPFD needed
- Avoid peak price hours 17-20 (0.25-0.30 €/kWh)

OUTPUT REQUIREMENTS:
Provide ONLY valid JSON with hourly LED allocations:
{
  "led_allocations": [hour0, hour1, hour2, ..., hour23]
}

FINAL VALIDATION: Ensure total daily PPFD = target ± 0.1%
```

**Results**: Improved accuracy and cost optimization, but some models provided explanatory text instead of pure JSON

### V3: Optimized for Pure JSON Output
**File**: `../data/test_sets/test_set_v3.json`

**Approach**: Refined V2 prompt with removal of validation instruction that encouraged explanatory responses
**Key Changes**:
- Removed "FINAL VALIDATION" line
- Maintained all other V2 enhancements
- Emphasized JSON-only output requirement

**Results**: Best performance across all metrics, 100% JSON compliance

## Performance Impact Analysis

### JSON Compliance Rates
| Version | Claude Opus 4 | Claude 3.7 Sonnet | Notes |
|---------|---------------|-------------------|-------|
| V1 | ~85% | ~90% | Basic compliance |
| V2 | ~95% | ~98% | Improved but some explanatory text |
| V3 | 100% | 100% | Perfect JSON compliance |

### Performance Metrics Comparison
| Metric | V1 (Baseline) | V2 (Enhanced) | V3 (Optimized) | Improvement |
|--------|---------------|---------------|----------------|-------------|
| Hourly MAE | ~55 | ~46 | ~32 | 42% reduction |
| Daily PPFD Error | ~450 | ~340 | ~285 | 37% reduction |
| Cost Efficiency | -12% | -9% | -4% | 67% improvement |
| Exact Matches | ~65% | ~79% | ~83% | 28% improvement |

## Key Insights

### What Worked
1. **Role Definition**: Establishing expertise context improved decision quality
2. **Algorithm Guidance**: Step-by-step instructions provided clear optimization framework
3. **Concrete Examples**: Specific scenarios helped models understand expected behavior
4. **Constraint Clarity**: Explicit parameter bounds reduced invalid outputs

### What Didn't Work
1. **Validation Instructions**: "FINAL VALIDATION" encouraged explanatory text over pure JSON
2. **Overly Complex Formatting**: Too many formatting instructions could confuse models
3. **Ambiguous Objectives**: Unclear prioritization between competing goals

### Critical Success Factors
1. **JSON-First Design**: Prioritize output format compliance from the start
2. **Incremental Testing**: Test each prompt enhancement individually
3. **Model-Specific Adaptation**: Different models respond to different prompt elements
4. **Clear Objective Hierarchy**: Explicitly state primary vs. secondary goals

## Prompt Engineering Best Practices

### For Optimization Tasks
1. **Define Expert Role**: Establish domain expertise context
2. **Provide Algorithm Framework**: Give step-by-step approach
3. **Include Concrete Examples**: Show expected behavior patterns
4. **Specify Output Format First**: Lead with format requirements
5. **Avoid Validation Requests**: Don't ask for explanations in structured output tasks

### For JSON Compliance
1. **Emphasize "ONLY" in Output Requirements**: Make exclusivity clear
2. **Remove Validation Instructions**: Avoid encouraging explanatory text
3. **Test Incrementally**: Validate JSON compliance at each prompt iteration
4. **Use Consistent Formatting**: Maintain standard JSON structure examples

### For Multi-Objective Optimization
1. **Establish Clear Hierarchy**: Primary objective first, constraints second
2. **Quantify Trade-offs**: Provide specific tolerance levels
3. **Give Prioritization Examples**: Show how to handle competing objectives
4. **Define Success Criteria**: Clear metrics for evaluation

## Future Prompt Development

### V4 Considerations
Potential enhancements for future prompt versions:
- **Seasonal Awareness**: Include seasonal optimization strategies
- **Uncertainty Handling**: Address variable electricity price scenarios
- **Multi-Day Planning**: Extend optimization horizon
- **Energy Storage**: Incorporate battery storage optimization

### Model-Specific Adaptations
Different models may benefit from:
- **Claude**: More structured, formal instructions
- **GPT**: Conversational, example-heavy approaches
- **Open Source**: Simpler, more direct instructions

### Evaluation Framework
For testing new prompt versions:
1. A/B test against V3 baseline
2. Measure JSON compliance first
3. Evaluate optimization quality second
4. Test across multiple model families
5. Validate statistical significance of improvements 