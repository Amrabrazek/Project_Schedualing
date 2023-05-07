 # Project_Schedualing
    #### Video Demo:  <https://youtu.be/0Yvh4jQpSF8>
    #### Description: The purpose of the project :Schedule a project which consists of some activities related somehow between each other
                      which will produce a Baseline plan with the amount of resources needed everyday.However, Nothing goes as planned
                      That why there would be an option to update the projects which is already made and compare the actual schedule and the planned one.

                      The Main Function: The main function gives you two options either to create a new project from scratch 
                      or update a current one and depending on
                      which path you take a number of function will run.

                      First path: Consists of 4 functions
                          1-  New_project which creates the project sqlite table and add activities.
                                  >it only take one argument which is the project name (CS50) in our case
                                  >it creates a sqlite table with this name where all the info is stored (ID, name, Duration, and Cost)
                                  >add all the activities that the user want one after another using a while true loop
                                  >each activity is an object as it's created by a class called activty class 

                          2- Schedule which schedule the project and get the critical path
                                  using "sche" function, all the possible paths will be listed using recursion.
                                  and then using the "project_critical_path" Function the cretical path will be identified
                                  with the project duration 

                          3- dates function will update the activities start date and end date (SD and ED) in the sqlite table 
                             and it will also provide a Gantt chart which highlight critical activities using the red color.

                          4 - cost_barchart function draw a bar chart which identify the amount of resources (money) needed everyday
                              and also shows the cumulative cost to a specific date using a line.


                      Second path: Consists of 1 function
                          1- update_project: It asks the user for the actual dates for the activities which has updates and accordingly
                          it draws a Gantt Chart comparing the actual and the planned schedule.
                          
                          
                    The test_project file is based on a pre created project called ("x") which i calculated manually
                          it makes sure that the cost is calculated right
                          it makes sure that the critical path is identified correctly
                          it also make sure the project duration is write 
                         






