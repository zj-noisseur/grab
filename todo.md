Perform reverse geoencoding where the user first types in their intended location, and the program outputs the closest resemblance to those and selects from the list of those choice.

Ideally, we should not handle the low level of rendering the layouts. So we will be using Questionary.

Workflow:
1. User selects the state
2. User types in the location they want, Nomanitim servers are polled with the search query (which are partial that we provided, queried once the user press a certain hotkey). Dropdown allows the user to choose the intended place, with the flexibility to amend the query and search again for much more accurate results.

Prompts:
1. Enter the pickup location
2. Enter the destination location
3. Select current weather condition (Choose from a hardcoded dropdown list of 3 values, ie sunny, cloudy, storm. Each of the 3 values are assigned a multipler score)
4. Select the current traffic condition (Congested, Normal, Free-flowing)
5. Final price is computed out (Distance * base_price * weather_multiplier * traffic_multiplier)



