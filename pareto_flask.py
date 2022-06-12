from flask import Flask, render_template, request, redirect, url_for, flash
import os
from fairpy.agents import AdditiveAgent
from fairpy.items.allocations_fractional import FractionalAllocation
from fairpy.items.pareto_improvement import ParetoImprovement

SECRET_KEY = os.urandom(32)

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        agents_count = request.form.get('agents')
        objects_count = request.form.get('objects')
        if not request.form['agents'] or not request.form['objects']:
            flash('Please fill all fields', 'error')
        else:
            return redirect(url_for('allocation',
                                    agents_count=int(agents_count),
                                    objects_count=int(objects_count)))
    return render_template('index.html')


@app.route('/allocation/<agents_count>/<objects_count>', methods=['GET', 'POST'])
def allocation(agents_count, objects_count):
    if request.method == 'POST':
        if not request.form['ag_input']:
            flash('Please fill all fields', 'error')
        else:
            user_input = request.form.getlist('ag_input')
            float_user_input = convert_arr_to_float(user_input)
            validation, validation_value = validate_user_input(int(agents_count), int(objects_count), float_user_input)
            if not validation:
                flash(f'Total sum of an object cannot exceed 1.0, for example on of your objects is {validation_value}', 'error')
            else:
                user_input = ','.join(user_input)
                return redirect(url_for('valuation',
                                        agents_count=int(agents_count),
                                        objects_count=int(objects_count),
                                        allocation_input=user_input))
    return render_template('allocation.html', agents=int(agents_count), objects=int(objects_count))


@app.route('/valuation/<agents_count>/<objects_count>/<allocation_input>', methods=['GET', 'POST'])
def valuation(agents_count, objects_count, allocation_input):
    if request.method == 'POST':
        if not request.form['ag_input']:
            flash('Please fill all fields', 'error')
        else:
            user_input = request.form.getlist('ag_input')
            user_input = ','.join(user_input)
            return redirect(url_for('calculation',
                                    agents_count=int(agents_count),
                                    objects_count=int(objects_count),
                                    allocation_input=allocation_input,
                                    valuation_input=user_input))
    return render_template('valuation.html',
                           agents=int(agents_count),
                           objects=int(objects_count))


@app.route('/calculation/<agents_count>/<objects_count>/<allocation_input>/<valuation_input>')
def calculation(agents_count, objects_count, allocation_input, valuation_input):
    allocations = convert_arr_to_float(allocation_input.split(','))
    valuations = convert_arr_to_float(valuation_input.split(','))
    agents_list = []
    agents_allocation_list = []
    index = 0
    for agent_i in range(int(agents_count)):
        agent_valuation_dict = {}
        agent_allocation_dict = {}
        for object_i in range(int(objects_count)):
            agent_valuation_dict[str(object_i)] = valuations[index]
            agent_allocation_dict[str(object_i)] = allocations[index]
            index += 1
        agents_list.append(AdditiveAgent(agent_valuation_dict, name=f'agent{agent_i}'))
        agents_allocation_list.append(agent_allocation_dict)
    fr_allocation = FractionalAllocation(agents_list, agents_allocation_list)
    pi = ParetoImprovement(fr_allocation, generate_items_set(objects_count))
    return render_template('calculation.html',
                           us_input=parse_output(str(fr_allocation)),
                           pi_result=parse_output(str(pi.find_pareto_improvement())))


@app.route('/about')
def about():
    return render_template('about.html')


def validate_user_input(agents: int, objects: int, user_input: list) -> (bool, float):
    """
    Validates the user input to see if there is no exceeding of the
    FractionalAllocation limtis

    :param agents: Number of agents in the allocation
    :param objects: Number of objects in the allocation
    :param user_input: The unser input list from the input form
    :return: True if the input is correct, False otherwise
    """
    results = {}
    index = 0
    for i in range(agents):
        for j in range(objects):
            tmp = user_input[index]
            if j in results.keys():
                results[j] += tmp
            else:
                results[j] = tmp
            index += 1
    for object_sum in results.values():
        if object_sum > 1:
            return False, object_sum
    return True, 0


def convert_arr_to_float(list_input: list) -> list:
    """
    converts the input list content to float

    :return: list[float]
    """
    result = []
    for i in range(0, len(list_input)):
        result.append(float(list_input[i]))
    return result


def generate_items_set(objects: int) -> set:
    """
    Generates the desired item set from the items index

    :return: Set of the desired items for calculations
    """
    result = set()
    for iten_name in range(int(objects)):
        result.add(str(iten_name))
    return result


def parse_output(str_input: str) -> list:
    """
    Parses the FractionalAllocation output in order to
    set if for HTML printing

    :return: list of features to print (str)
    """
    result = []
    for content in str_input.split('agent'):
        result.append(f"agent{content.replace('value','   |   Total value')}")
    return result[1:]


if __name__ == "__main__":
    app.run()
