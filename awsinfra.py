#!/usr/bin/python
#
# Copyright 2014. @RoaldIT
__author__ = '@RoaldIT'
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Usage: python awsinfra --{start|stop|status}=[I[List of Instance IDs]],[V]
#
# e.g:  python awsinfra --status=I,V                                            ->  List all instances and vpns
# awsinfra --status=V                                                     	->  List all vpns
# awsinfra --status=I{r-ec999de4,r-ec999de5},V                            	->  List only instances IDs and vpns
#
# Vpn in this version is hardcoded (e.g. Customer Private Gateway, Virtual Private Gateway, CIDR, etc.)
# Vpn doesn't allow list of IDs


# Import libraries
import sys
import getopt
import time

# Import the SDK
import boto.ec2
import boto.vpc

# Initiate global variables
strRegion = 'us-west-2'


def main(argv):
    try:
        myopts, args = getopt.getopt(argv[1:], '', ['start=', 'stop=', 'status='])
    except getopt.GetoptError as e:
        print(str(e))
        print('Usage: %s --{start|stop|status}=[I[List of Instance IDs]],[V]' % sys.argv[0])
        sys.exit(2)

    # Connect AWS ec2 region
    ec2 = connect_region('ec2')

    # Connect AWS vpc region
    vpc = connect_region('vpc')

    opt = ''
    ids = []
    for l in range(len(myopts)):
        if l == 0:
            opt = myopts[l][0]
            ids.append(myopts[l][1])
        else:
            ids.append(myopts[l][1])

    if opt == '--start':
        f_start(ec2, vpc, ids)
    elif opt == '--stop':
        f_stop(ec2, vpc, ids)
    elif opt == '--status':
        f_status(ec2, vpc, ids)

    return


def connect_region(service):
    # Instantiate a new client for Amazon Elastic Compute Cloud (EC2). With no
    # parameters or configuration, the AWS SDK for Python (Boto) will look for
    # access keys in these environment variables:
    #
    # AWS_ACCESS_KEY_ID='...'
    # AWS_SECRET_ACCESS_KEY='...'
    #
    # For more information about this interface to Amazon EC2, see:
    # http://boto.readthedocs.org/en/latest/ec2_tut.html
    if service == 'ec2':
        return boto.ec2.connect_to_region(strRegion)
    elif service == 'vpc':
        return boto.vpc.connect_to_region(strRegion)


def c_object_list(objects):
    """

    :param objects:
    :return:
    """
    instance_list = []
    instance_print = False
    vpn_list = []
    vpn_print = False
    objects_list = []

    # Split list of objects passed as parameters
    for l1 in range(len(objects)):
        objects_split = objects[l1].split(',')
        for l2 in range(len(objects_split)):
            objects_list.append(objects_split[l2])

    for o in objects_list:
        if o[:1] == 'I':
            instance_print = True
            instance_list.append(o[1:].translate(None, '{}'))
        elif o[:1] == 'V':
            vpn_print = True
            vpn_list.append(o[1:].translate(None, '{}'))
        else:
            if instance_print:
                instance_list.append(o.translate(None, '{}'))
            elif vpn_print:
                vpn_list.append(o.translate(None, '{}'))

    return instance_list, instance_print, vpn_list, vpn_print


def f_start(ec2, vpc, objects):
    # Create list of objects to print
    instance_list, instance_print, vpn_list, vpn_print = c_object_list(objects)

    if instance_print:
        # Start instance
        print('Instance Starting Process >>>')
        instances = ec2.get_all_instances()
        for inst in instances:
            if inst.instances[0].id in instance_list or len(instance_list[0]) == 0:
                if inst.instances[0].state == 'running':
                    print('ID: ' + inst.instances[0].id + ' is already running.')
                elif inst.instances[0].state == 'stopped':
                    ec2.start_instances(instance_ids=inst.instances[0].id)
                    print('ID: ' + inst.instances[0].id + ' has been started.')
                else:
                    print('ID: ' + inst.instances[0].id + ' is under the ' + inst.instances[0].state + ' state.')

    if vpn_print:
        # Create vpn (The list of vpn IDs is irrelevant in this case as they are being created)
        print('\n' + 'Vpn Starting Process >>>')
        vpn_available = False
        vpns = vpc.get_all_vpn_connections()
        for v in vpns:
            if v.vpn_gateway_id == 'vgw-2271ac3c' and v.state == 'available':
                vpn_available = True
                print('ID: ' + v.id + ' is already available.')
                break

        if not vpn_available:
            vpc.create_vpn_connection('ipsec.1', 'cgw-5172af4f', 'vgw-2271ac3c', static_routes_only=True, dry_run=False)
            # Wait 30s before start trying to set the static route
            time.sleep(30)
            for tries in range(45):     # This give a maximum waiting time of 300s
                vpns_retry = vpc.get_all_vpn_connections()
                for v_retry in vpns_retry:
                    if v_retry.vpn_gateway_id == 'vgw-2271ac3c' and v_retry.state == 'available':
                        vpn_available = True
                        print('ID: ' + v_retry.id + ' is available.')
                        # Create static route for the local network
                        vpc.create_vpn_connection_route('10.0.0.0/16', v_retry.id, dry_run=False)
                        # Exit for loop
                        break

                if vpn_available:
                    # Exit for loop
                    break
                else:
                    # Sleep 6s before another try
                    time.sleep(6)
    return


def f_stop(ec2, vpc, objects):
    # Create list of objects to print
    instance_list, instance_print, vpn_list, vpn_print = c_object_list(objects)

    if instance_print:
        # Stop instance
        print('Instance Stopping Process >>>')
        instances = ec2.get_all_instances()
        for inst in instances:
            if inst.instances[0].id in instance_list or len(instance_list[0]) == 0:
                if inst.instances[0].state == 'running':
                    ec2.stop_instances(instance_ids=inst.instances[0].id)
                    print('ID: ' + inst.instances[0].id + ' has been stopped.')
                elif inst.instances[0].state == 'stopped':
                    print('ID: ' + inst.instances[0].id + ' is already stopped.')
                else:
                    print('ID: ' + inst.instances[0].id + ' is under the ' + inst.instances[0].state + ' state.')

    if vpn_print:
        # Print vpn information
        print('\n' + 'Vpn Stopping Process >>>')
        vpns = vpc.get_all_vpn_connections()
        for v in vpns:
            if v.state == 'available':
                vpc.delete_vpn_connection(v.id, dry_run=False)
                print('ID: ' + v.id + ' has been deleted.')
            elif v.state == 'deleted':
                print('ID: ' + v.id + ' is already deleted.')
            else:
                print('ID: ' + v.id + ' is under the ' + v.state + ' state.')

    return


def f_status(ec2, vpc, objects):
    # Create list of objects to print
    instance_list, instance_print, vpn_list, vpn_print = c_object_list(objects)

    if instance_print:
        # Print instance information
        print('Instance Status >>>')
        instances = ec2.get_all_instances()
        for inst in instances:
            if inst.instances[0].id in instance_list or len(instance_list[0]) == 0:
                print('ID: ' + inst.instances[0].id + '\t\t\t\t' + 'State: ' + inst.instances[0].state)

    if vpn_print:
        # Print vpn information
        print('\n' + 'Vpn Status >>>')
        vpns = vpc.get_all_vpn_connections()
        for v in vpns:
            print('ID: ' + v.id + '\t\t\t' + 'State: ' + v.state)

    return

# Call main()
if __name__ == "__main__":
    # Set debug True in order to debug using IDLE
    debug = False
    if debug:
        sys.argv = ['arg0', '--status=I{i-93438d9c,i-f013d9ff,r-ec999de5},V']

    main(sys.argv)    
