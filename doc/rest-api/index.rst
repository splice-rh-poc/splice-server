REST API
========

.. toctree::
   :maxdepth: 2

.. http:post:: /api/v1/entitlement/(str:uuid)/

   Process a splice checkin and request an entitlement cert for installed
   products.

   **Sample request**:

   .. sourcecode:: http

      POST /api/v1/entitlement/(str:uuid)/ HTTP/1.1
      Host: example.com
      Accept: application/json

      {
        'consumer_identifier': '52:54:00:15:E7:69',
        'products': ['40', '41'],
        'system_facts': {'tbd': 'values'}
      }
  
   **Sample Response**:

   .. sourcecode:: http

      HTTP/1.0 200 OK
      Content-Type: application/json

      {
        'certs': [[<Entitlement Certificate Value>]],
         'consumer_identifier': '52:54:00:15:E7:69',
         'message': '',
         'products': ['40', '41'],
         'resource_uri': '',
         'system_facts': {'tbd': 'values'}
      }

   :statuscode 200: Ok

.. http:post:: /api/v1/productusage/

   Import product usage into the splice server.

   **Sample Request**:

   .. sourcecode:: http

      POST /api/v1/productusage/ HTTP/1.1
      Host: example.com
      Accept: application/json

      [
         {
            "splice_server" : "splice_server_uuid-1",
            "allowed_product_info" : [
               "69"
            ],
            "unallowed_product_info" : [ ],
            "facts" : {
               "lscpu_dot_cpu(s)" : "1",
               "memory_dot_memtotal" : "604836",
               "lscpu_dot_cpu_socket(s)" : "1"
            },
            "instance_identifier" : "12:31:3D:08:40:00",
            "date" : ISODate("2012-10-26T02:00:00Z"),
            "consumer" : "8d401b5e-2fa5-4cb6-be64-5f57386fda86"
         }
         {
            "splice_server" : "splice_server_uuid-1",
            "allowed_product_info" : [
               "69",
               "183"
            ],
            "unallowed_product_info" : [ ],
            "facts" : {
               "lscpu_dot_cpu(s)" : "1",
               "memory_dot_memtotal" : "604836",
               "lscpu_dot_cpu_socket(s)" : "1"
            },
            "instance_identifier" : "12:31:3D:08:40:00",
            "date" : ISODate("2012-10-26T02:00:00Z"),
            "consumer" : "fea363f5-af37-4a23-a2fd-bea8d1fff9e8"
         }
      ]

   **Sample Response**:

   .. sourcecode:: http

      HTTP/1.0 202 Accepted
      Content-Type: application/json

   :statuscode 202: Accepted

.. http:post:: /api/v1/marketingproductusage/

   Import marketing product usage into the splice server.

   **Sample Request**:

   .. sourcecode:: http

      POST /api/v1/marketingproductusage/ HTTP/1.1
      Host: example.com
      Accept: application/json

      {
        "objects": [{
        "updated": "2013-03-06T00:00:00Z",
        "splice_server": "ec2-23-20-217-133.compute-1.amazonaws.com",
        "facts": {
            "net_dot_interface_dot_lo_dot_mac_address": "00:00:00:00:00:00",
            "memory_dot_memtotal": "604160",
            "lscpu_dot_on-line_cpu(s)_list": "",
            "lscpu_dot_l1d_cache": "6144 KB",
            "systemid": "1000010003",
            "net_dot_interface_dot_eth0_dot_ipv4_netmask": "255.255.254.0",
            "lscpu_dot_architecture": "x86_64",
            "lscpu_dot_model": "Intel(R) Xeon(R) CPU           E5430  @ 2.66GHz",
            "net_dot_interface_dot_lo_dot_ipv4_broadcast": "10.243.3.255",
            "lscpu_dot_cpu_op-mode(s)": "",
            "uname_dot_machine": "x86_64",
            "lscpu_dot_l3_cache": "",
            "lscpu_dot_core(s)_per_socket": "1",
            "lscpu_dot_cpu_family": "",
            "lscpu_dot_cpu(s)": "1",
            "lscpu_dot_l1i_cache": "",
            "lscpu_dot_virtualization_type": "",
            "net_dot_interface_dot_lo_dot_ipv4_address": "127.0.0.1",
            "cpu_dot_cpu_socket(s)": "0",
            "cpu_dot_cpu(s)": "1",
            "net_dot_ipv4_address": "10.243.2.179",
            "lscpu_dot_bogomips": "",
            "lscpu_dot_l2_cache": "",
            "memory_dot_swaptotal": "0",
            "net_dot_interface_dot_eth0_dot_ipv4_address": "10.243.2.179",
            "lscpu_dot_stepping": "10",
            "lscpu_dot_cpu_mhz": "2659",
            "net_dot_interface_dot_eth0_dot_mac_address": "12:31:3b:02:01:45",
            "lscpu_dot_hypervisor_vendor": "",
            "lscpu_dot_vendor_id": "GenuineIntel",
            "net_dot_interface_dot_lo_dot_ipv4_netmask": "255.0.0.0",
            "lscpu_dot_byte_order": "",
            "lscpu_dot_cpu_socket(s)": "0"
        },
        "created": "2013-03-06T00:00:00Z",
        "entitlement_status": "partial",
        "product_info": [
            {
                "account": "1212729",
                "product": "SYS0395",
                "contract": "2595500",
                "quantity": 1,
                "sla": "prem",
                "support_level": "l1-l3"
            }
        ],
        "instance_identifier": "608626c6-ee7b-4c21-92f7-f769ff230b46",
        "date": "2013-03-06T16:32:52Z"
        }]
      }

   **Sample Response**:

   .. sourcecode:: http

      HTTP/1.0 204 No Content
      Content-Type: application/json

   :statuscode 204: No Content

.. http:post:: /api/v1/spliceserver/

   Import metadata about other splice server instances into this splice server.

   **Sample Request**:

   .. sourcecode:: http

      POST /api/v1/spliceserver/ HTTP/1.1
      Host: example.com
      Accept: application/json


      {
        "objects": [
            {
                "environment": "us-east-1a", 
                "hostname": "example.com", 
                "description": "A test splice server instance",
                "uuid": "uuid_value_B",
                "created": "2012-12-07T15:35:54.686000",
                "updated": "2012-12-07T15:35:54.686000"
            },
            {
                "environment": "us-east-1a", 
                "hostname": "example.com", 
                "description": "A test splice server instance",
                "uuid": "uuid_value_A",
                "created":  "2012-12-07T15:35:54.686000",
                "updated": "2012-12-07T15:35:54.686000"
            }
        ]
      }

   **Sample Response**:

   .. sourcecode:: http

      HTTP/1.0 204 No Content
      Content-Type: application/json

   :statuscode 204: No Content

.. http:post:: /api/v1/product/

   Import product metadata into the splice server.

   **Sample Request**:

   .. sourcecode:: http

      POST /api/v1/product/ HTTP/1.1
      Host: example.com
      Accept: application/json


      {
        "objects": [
            {
                "updated": "2013-02-27 21:26:34.130000+00:00", 
                "product_id": "85", 
                "created": "2013-02-27 21:26:34.130000+00:00", 
                "engineering_ids": [
                    "368", 
                    "366", 
                    "364", 
                    "365", 
                    "367", 
                    "363"
                ], 
                "eng_prods": [
                    {
                        "vendor": "Red Hat", 
                        "id": "368", 
                        "name": "Red Hat Enterprise Linux Load Balancer (for RHEL 6 Server) (Source RPMs)", 
                        "label": "rhel-lb-for-rhel-6-server-source-rpms"
                    }, 
                    {
                        "vendor": "Red Hat", 
                        "id": "366", 
                        "name": "Red Hat Enterprise Linux Load Balancer (for RHEL 6 Server) (Debug RPMs)", 
                        "label": "rhel-lb-for-rhel-6-server-debug-rpms"
                    }, 
                    {
                        "vendor": "Red Hat", 
                        "id": "364", 
                        "name": "Red Hat Enterprise Linux Load Balancer (for RHEL 6 Server) Beta (RPMs)", 
                        "label": "rhel-lb-for-rhel-6-server-beta-rpms"
                    }, 
                    {
                        "vendor": "Red Hat", 
                        "id": "365", 
                        "name": "Red Hat Enterprise Linux Load Balancer (for RHEL 6 Server) Beta (Source RPMs)", 
                        "label": "rhel-lb-for-rhel-6-server-beta-source-rpms"
                    }, 
                    {
                        "vendor": "Red Hat", 
                        "id": "367", 
                        "name": "Red Hat Enterprise Linux Load Balancer (for RHEL 6 Server) (RPMs)", 
                        "label": "rhel-lb-for-rhel-6-server-rpms"
                    }, 
                    {
                        "vendor": "Red Hat", 
                        "id": "363", 
                        "name": "Red Hat Enterprise Linux Load Balancer (for RHEL 6 Server) Beta (Debug RPMs)", 
                        "label": "rhel-lb-for-rhel-6-server-beta-debug-rpms"
                    }
                ], 
                "attrs": {
                    "arch": "x86_64,x86", 
                    "type": "SVC", 
                    "name": "Red Hat Enterprise Linux Load Balancer (for RHEL Server)"
                }, 
                "dependent_product_ids": [], 
                "name": "Red Hat Enterprise Linux Load Balancer (for RHEL Server)"
        }]
      }

   **Sample Response**:

   .. sourcecode:: http

      HTTP/1.0 204 No Content
      Content-Type: application/json

   :statuscode 204: No Content

.. http:post:: /api/v1/pools/

   Import pools metadata into the splice server.

   **Sample Request**:

   .. sourcecode:: http

      POST /api/v1/pools/ HTTP/1.1
      Host: example.com
      Accept: application/json

      
      { "objects": [
        {
          "provided_products": [
            {
              "id": "90", 
              "name": "Red Hat Enterprise Linux Resilient Storage (for RHEL Server)"
            }, 
            {
              "id": "83", 
              "name": "Red Hat Enterprise Linux High Availability (for RHEL Server)"
            }, 
            {
              "id": "85", 
              "name": "Red Hat Enterprise Linux Load Balancer (for RHEL Server)"
            }, 
            {
              "id": "69", 
              "name": "Red Hat Enterprise Linux Server"
            }, 
            {
              "id": "71", 
              "name": "Red Hat Enterprise Linux Workstation"
            }
          ], 
          "account": "1212729", 
          "uuid": "8ad597ee3d1d8c2b013d1d8cc18c0023", 
          "end_date": "2022-01-01 04:59:59+00:00", 
          "created": "2013-02-27 21:26:36.684000+00:00", 
          "updated": "2013-02-27 21:26:36.684000+00:00", 
          "contract": null, 
          "product_name": "Red Hat Employee Subscription", 
          "product_attributes": {
            "name": "Red Hat Employee Subscription", 
            "support_level": "None", 
            "support_type": "None", 
            "variant": "Employee Subscription", 
            "option_code": "30", 
            "subtype": "None", 
            "virt_limit": "unlimited", 
            "enabled_consumer_types": "SAM", 
            "type": "MKT", 
            "sockets": "128", 
            "product_family": "Red Hat Enterprise Linux", 
            "description": "Red Hat Enterprise Linux"
          }, 
          "product_id": "SYS0395", 
          "active": true, 
          "start_date": "2011-10-11 04:00:00+00:00", 
          "quantity": 2
        }]
      }

   **Sample Response**:

   .. sourcecode:: http

      HTTP/1.0 204 No Content
      Content-Type: application/json

   :statuscode 204: No Content

.. http:post:: /api/v1/rules/

   Import rules metadata into the splice server.

   **Sample Request**:

   .. sourcecode:: http

      POST /api/v1/rules/ HTTP/1.1
      Host: example.com
      Accept: application/json

      {
        "objects": [{
          "version": "0",
          "data": "json rules as string here"
        }]

      }

   **Sample Response**:

   .. sourcecode:: http

      HTTP/1.0 204 No Content
      Content-Type: application/json

   :statuscode 204: No Content

