using MacroEnergy
using Gurobi

(case, solution) = run_case(@__DIR__; 
    optimizer=Gurobi.Optimizer,
    optimizer_attributes=("Method" => 2, "Crossover" => 0, "BarConvTol" => 1e-3, "BarHomogeneous" => 1)
);

#(case, solution) = run_case(
#    @__DIR__;
#    planning_optimizer=Gurobi.Optimizer, # Optimizer Constructor for the planning problem
#    subproblem_optimizer=Gurobi.Optimizer, # Optimizer Constructor for the subproblems
#    planning_optimizer_attributes=("Method" => 2, "Crossover" => 0, "BarConvTol" => 1e-3, "BarHomogeneous" => 1), # Optimizer Settings for the planning problem
#    subproblem_optimizer_attributes=("Method" => 2, "Crossover" => 0, "BarConvTol" => 1e-3, "BarHomogeneous" => 1), # Optimizer Settings for the subproblems
#);