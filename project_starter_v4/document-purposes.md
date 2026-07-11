                                                                                    
  ### logging-spec.md                                                                 
  ...                                                       
  Update when:                                                                        
  * New modules are added (add one line to the Module Naming Convention table)        
  * Log format changes                                                                
  * Logger instantiation pattern changes                                              
                                                                                      
  AGENTS.md line 284 明寫 logging-spec.md Module Naming Convention table 是 Document  
  Update Checklist trigger。New modules + log format 都應該 Doc Check 過濾再加      
  qualifier。                                                                         
                                                            
  3. log-[module].md (line 224-236) — 「Update immediately if function names change」 
  跟 Module Completion Check rule 矛盾
                                                                                      
  Generate when the module is complete (see AGENTS.md → Module Completion Check).
  Update immediately if function names or file paths change.                          
                                                                                      
  AGENTS.md line 218-220：Do NOT create or update [module]-module-data-flow.md or     
  [module]-flow.md during a task unless the module is 100% complete. 雖然這 rule      
  字面是講 *-module-data-flow.md 和 *-flow.md，沒明寫 log-[module].md — 但 spirit     
  應該一致（同樣是 Module Completion Check 時做的東西）。                           
                                                                                    
  「Update immediately if function names change」會讓 agent 在 mid-task 改 log 點 — 跟
   Module Completion Check 的「不一次做完 module 之前別動」衝突。
                                                                                      
  修法改 wording：                                          
  Update at module completion (see AGENTS.md → Module Completion Check).            
  Track changes during development in your head — apply the updates when the module   
  reaches completion.                                                                 
                                                                                      
